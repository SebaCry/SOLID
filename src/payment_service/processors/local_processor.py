import uuid

from payment_service.commons import CustomerData, PaymentResponse, PaymentData

from .payment import PaymentProcessorProtocol
from .recurring import RecurringPaymentProtocol
from .refunds import RefundPaymentProtocol

class LocalPaymentProcessor(PaymentProcessorProtocol, RecurringPaymentProtocol, RefundPaymentProtocol):
    def process_payment(self, customer_data:CustomerData, payment_data: PaymentData) -> PaymentResponse:
        print(f"Processing local payment for {customer_data.name}")
        transaction_id = f"local-transaction-id-{uuid.uuid4()}"
        return PaymentResponse(
            status="success",
            amount=payment_data.amount,
            transaction_id=transaction_id,
            message="Papu papu"
        )

    def refund_payment(self, transaction_id: str) -> PaymentResponse:
        print(f"Refund with transaction_id: {transaction_id}")
        return PaymentResponse(
            status="success",
            amount=0,
            transaction_id=transaction_id,
            message="Reembolso realizado xdd"
        )