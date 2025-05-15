from decorator_procotol import PaymentServiceDecoratorProtocol
from decorator_procotol import PaymentServiceProtocol
from dataclasses import dataclass

from .commons import CustomerData, PaymentData, PaymentResponse

@dataclass
class PaymentServiceLogging(PaymentServiceDecoratorProtocol):
    wrapped = PaymentServiceProtocol

    def process_transaction(
        self, customer_data: CustomerData, payment_data: PaymentData
    ) -> PaymentResponse: 
        print('Start process transaction')

        response = self.wrapped.process_transaction(customer_data, payment_data)
        print('Finish process transaction')
        return response

    def process_refund(self, transaction_id: str): 
        print(f'Start process refund: {transaction_id}')

        response = self.wrapped.process_refund(transaction_id)

        print('Finish process refund')
        return response

    def setup_recurring(
        self, customer_data: CustomerData, payment_data: PaymentData
    ): 
        print(f'Start process recurring ')

        print('Finish process refund')