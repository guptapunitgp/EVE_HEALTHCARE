import hashlib
import hmac

from app.services.payment_security import verify_checkout_signature, verify_webhook_signature


def test_checkout_signature_matches_razorpay_order_payment_pair():
    secret = "unit-test-secret"
    payload = b"order_123|pay_456"
    signature = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    assert verify_checkout_signature(secret, "order_123", "pay_456", signature)
    assert not verify_checkout_signature(secret, "order_other", "pay_456", signature)


def test_webhook_signature_checks_raw_body_and_rejects_missing_secret():
    secret = "unit-test-secret"
    payload = b'{"event":"payment.captured"}'
    signature = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    assert verify_webhook_signature(secret, payload, signature)
    assert not verify_webhook_signature(secret, payload + b" ", signature)
    assert not verify_webhook_signature("", payload, signature)
