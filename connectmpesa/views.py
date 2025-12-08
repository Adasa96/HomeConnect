from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from .models import PaymentRequest, MpesaTransaction


@login_required
def start_payment(request):
    if request.method == 'POST':
        amount = request.POST.get('amount')
        phone = request.POST.get('phone')
        if not amount or not phone:
            return HttpResponseBadRequest('Missing amount or phone')

        pr = PaymentRequest.objects.create(user=request.user, amount=amount, phone_number=phone)

        # Placeholder: integrate with real M-Pesa API here.
        # For now we mark as SENT and return a fake checkout id.
        pr.status = PaymentRequest.STATUS_SENT
        pr.checkout_request_id = f"SIMULATED-{pr.pk}-{int(pr.created_at.timestamp())}"
        pr.save()

        return JsonResponse({'status': 'ok', 'checkout_request_id': pr.checkout_request_id, 'request_id': pr.pk})

    return render(request, 'connectmpesa/start_payment.html')


@csrf_exempt
def mpesa_callback(request):
    # M-Pesa provider would POST JSON to this endpoint with transaction details
    if request.method != 'POST':
        return HttpResponseBadRequest('Only POST allowed')

    try:
        payload = request.body.decode('utf-8')
        import json
        data = json.loads(payload)
    except Exception:
        return HttpResponseBadRequest('Invalid JSON')

    # Expected keys (depending on provider) might include 'CheckoutRequestID', 'MpesaReceiptNumber', 'ResultCode', 'ResultDesc', 'Amount'
    checkout_id = data.get('CheckoutRequestID') or data.get('checkout_request_id')
    receipt = data.get('MpesaReceiptNumber') or data.get('mpesa_transaction_id')
    amount = data.get('Amount') or data.get('amount')
    result_code = data.get('ResultCode') or data.get('result_code')
    result_desc = data.get('ResultDesc') or data.get('result_desc')

    payment_request = None
    if checkout_id:
        try:
            payment_request = PaymentRequest.objects.filter(checkout_request_id=checkout_id).first()
        except Exception:
            payment_request = None

    # create transaction
    txn = MpesaTransaction.objects.create(
        payment_request=payment_request,
        mpesa_transaction_id=receipt or f"UNK-{checkout_id or 'no-checkout'}",
        amount=amount or 0,
        result_code=result_code,
        result_desc=result_desc,
        raw_payload=data,
    )

    if payment_request:
        if str(result_code) == '0' or result_code == 0:
            payment_request.status = PaymentRequest.STATUS_COMPLETED
        else:
            payment_request.status = PaymentRequest.STATUS_FAILED
        payment_request.save()

    return JsonResponse({'received': True, 'transaction_id': txn.mpesa_transaction_id})
