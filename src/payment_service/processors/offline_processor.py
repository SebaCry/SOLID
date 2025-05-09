import uuid

from .payment import PaymentProcessorProtocol
from payment_service.commons import CustomerData, PaymentData, PaymentResponse

class OfflinePaymentProcessor(PaymentProcessorProtocol):
    def process_transaction(
        self, customer_data: CustomerData, payment_data: PaymentData
    ) -> PaymentResponse:
        print("Processing offline payment for", customer_data.name)
        return PaymentResponse(
            status="success",
            amount=payment_data.amount,
            transaction_id=str(uuid.uuid4()),
            message="Offline payment success",
        )