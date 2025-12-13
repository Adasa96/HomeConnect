from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt

from .models import PaymentRequest, MpesaTransaction
from .forms import MpesaPaymentForm
from django_daraja.mpesa.core import MpesaClient

@login_required
def start_payment(request):
    if request.method == 'POST':
        amount = request.POST.get('amount')
        phone = request.POST.get('phone')  # name matches your form

        if not amount or not phone:
            return JsonResponse({'status': 'error', 'message': 'Amount and phone number are required.'})

        # Optionally: create payment record with "pending" status
        payment_request = PaymentRequest.objects.create(
            user=request.user,
            amount=amount,
            phone_number=phone,
            status=PaymentRequest.STATUS_PENDING
        )

        # Use daraja to initiate STK push
        cl = MpesaClient()
        try:
            response = cl.stk_push(
                phone_number=phone,
                amount=int(amount),
                account_reference=f"Invoice-{payment_request.pk}",
                transaction_desc="Payment for HomeConnect service",
                callback_url = request.build_absolute_uri(
                    # e.g. the endpoint you'll create to handle callbacks
                    # assumes you have named it 'mpesa_callback'
                    # adjust accordingly
                    '/mpesa/callback/'
                )
            )
        except Exception as e:
            # error from daraja client
            return JsonResponse({'status': 'error', 'message': str(e)})

        # Example response handling
        resp_data = response.json() if hasattr(response, 'json') else response

        # Optionally: save CheckoutRequestID in payment_request
        payment_request.checkout_request_id = resp_data.get('CheckoutRequestID')
        payment_request.save()

        # Return JSON to frontend
        return JsonResponse({
            'status': 'ok',
            'checkout_request_id': payment_request.checkout_request_id,
            'merchant_request_id': resp_data.get('MerchantRequestID'),
            'message': resp_data.get('CustomerMessage', 'STK Push sent')
        })

    # GET: render form
    return render(request, 'connectmpesa/start_payment.html', {})

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

@login_required
def payment_status(request, pk):
    """
    Return the current status of a payment request.
    """
    try:
        payment = PaymentRequest.objects.get(pk=pk, user=request.user)
    except PaymentRequest.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Payment not found'})

    return JsonResponse({
        'status': 'ok',
        'payment_status': payment.status
    })
