from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt

from .models import PaymentRequest, MpesaTransaction
from .forms import MpesaPaymentForm

# Start a Payment
@login_required
def start_payment(request):
    """
    Show a form to start a payment or process a submitted payment request.
    """
    if request.method == 'POST':
        amount = request.POST.get('amount')
        phone = request.POST.get('phone_number')

        if not amount or not phone:
            return HttpResponseBadRequest("Missing amount or phone number.")

        # Create payment request
        payment_request = PaymentRequest.objects.create(
            user=request.user,
            amount=amount,
            phone_number=phone
        )

        # Simulate sending to M-Pesa (replace this with real API integration)
        payment_request.status = PaymentRequest.STATUS_SENT
        payment_request.checkout_request_id = f"SIM-{payment_request.pk}-{int(payment_request.created_at.timestamp())}"
        payment_request.save()

        return JsonResponse({
            'status': 'ok',
            'checkout_request_id': payment_request.checkout_request_id,
            'request_id': payment_request.pk
        })

    # GET request - show form
    form = MpesaPaymentForm()
    return render(request, 'connectmpesa/start_payment.html', {'form': form})


# M-Pesa Callback Endpoint
@csrf_exempt
def mpesa_callback(request):
    """
    Endpoint for M-Pesa to send transaction results.
    Expects JSON POST containing checkout ID, receipt, result code, etc.
    """
    if request.method != 'POST':
        return HttpResponseBadRequest("POST method required.")

    import json
    try:
        data = json.loads(request.body)
    except Exception:
        return HttpResponseBadRequest("Invalid JSON payload.")

    checkout_id = data.get('CheckoutRequestID') or data.get('checkout_request_id')
    receipt = data.get('MpesaReceiptNumber') or data.get('mpesa_transaction_id')
    amount = data.get('Amount') or data.get('amount')
    result_code = data.get('ResultCode') or data.get('result_code')
    result_desc = data.get('ResultDesc') or data.get('result_desc')

    # Find the corresponding payment request (if any)
    payment_request = PaymentRequest.objects.filter(checkout_request_id=checkout_id).first()

    # Save transaction record
    txn = MpesaTransaction.objects.create(
        payment_request=payment_request,
        mpesa_transaction_id=receipt or f"UNK-{checkout_id or 'no-checkout'}",
        amount=amount or 0,
        result_code=result_code,
        result_desc=result_desc,
        raw_payload=data
    )

    # Update payment request status
    if payment_request:
        if str(result_code) in ['0', 0]:
            payment_request.status = PaymentRequest.STATUS_COMPLETED
        else:
            payment_request.status = PaymentRequest.STATUS_FAILED
        payment_request.save()

    return JsonResponse({'received': True, 'transaction_id': txn.mpesa_transaction_id})

# Optional: List User Payment Requests
@login_required
def payment_history(request):
    """
    Show all M-Pesa payment requests for the logged-in user.
    """
    requests = PaymentRequest.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'connectmpesa/payment_history.html', {'requests': requests})
