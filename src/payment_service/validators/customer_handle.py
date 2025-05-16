from chain_handle import ChainHandler
from commons import Request
from .customer import CustomerValidator
from .payment import PaymentDataValidator

class CustomerHandler(ChainHandler):
    def handle(self, request: Request):
        validator = CustomerValidator()
        try:
            validator.validate(request.customer_data)
            if self._next_handlrer:
                self._next_handlrer.handle(request)
                 
        except ValueError as e:
            print(f"Error: {e}")

class PaymentHandler(ChainHandler):
    def handle(self, request: Request):
        validator = PaymentDataValidator()
        try:
            validator.validate(request.payment_data)
            if self._next_handlrer:
                self._next_handlrer.handle(request)
        except ValueError as e:
            print(f"Error: {e}")  