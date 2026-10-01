import hashlib
import hmac


def verify_webhook_signature(secret: str, raw_body: bytes, signature: str) -> bool:
    if not secret or not signature:
        return False
    expected = hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def verify_checkout_signature(secret: str, order_id: str, payment_id: str, signature: str) -> bool:
    if not secret or not signature:
        return False
    signed_payload = f"{order_id}|{payment_id}".encode()
    expected = hmac.new(secret.encode(), signed_payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)
