
import os
from dataclasses import dataclass, field
from typing import Optional, Protocol
import uuid
import stripe
from dotenv import load_dotenv
from pydantic import BaseModel
from stripe import Charge
from stripe.error import StripeError

_ = load_dotenv()

class ContactInfo(BaseModel):
    email: Optional[str] = None
    phone: Optional[str] = None

class CustomerData(BaseModel):
    name: str
    contact_info: ContactInfo
    customer_id : Optional[str] = None

class PaymentData(BaseModel):
    amount: int
    source: str

class PaymentResponse(BaseModel):
    status: str
    amount: int
    transaction_id : Optional[str] = None
    message: Optional[str] = None

class PaymentProcessor(Protocol):
    """
    Protocol for processing payments, refunds, and recurring payments.
    # HEREDA A TODOS LOS PAYMENTPROCESOR
    This protocol defines the interface for payment processors. Implementations
    should provide methods for processing payments, refunds, and setting up recurring payments.
    """
    def process_transaction(
        self, customer_data: CustomerData, payment_data: PaymentData
    ) -> PaymentResponse: ...

    def refund_payment(self, transaction_id:str) -> PaymentResponse: ...

    def setup_recurring_payment(
            self, customer_data: CustomerData, payment_data: PaymentData
    ) -> PaymentResponse: ...

class StripePaymentProcessor(PaymentProcessor):
    def process_transaction(self, customer_data: CustomerData, payment_data: PaymentData) -> PaymentResponse:
        stripe.api_key = os.getenv('STRIPE_API_KEY')
        try:
            charge = stripe.Charge.create(
                amount = payment_data.amount,
                currency = 'usd',
                source = payment_data.source,
                description = f'Charge for {customer_data}'
            )
            print('Payment succesful')
            return PaymentResponse(
                status=charge['status'],
                amount=charge['amount'],
                transaction_id=['id'],
                message= 'Payment succesful'
            )
        except StripeError as e:
            print(f'Payment failed: {e}')
            return PaymentResponse(
                status='failed',
                amount=payment_data.amount,
                transaction_id=None,
                message=str(e)
            )

    def refund_payment(self, transaction_id:str) -> PaymentResponse:
        stripe.api_key= os.getenv('STRIPE_API_KEY')
        try:
            refund = stripe.Refund.create(charge=transaction_id)
            print('Refund succesful')
            return PaymentResponse(
                status=refund['status'],
                amount=refund['amount'],
                transaction_id=refund['id'],
                message='Refund succesful'
            )
        except StripeError as e:
            print(f'Refund Failed {e}')
            return PaymentResponse(
                status="failed",
                amount=0,
                transaction_id=None,
                message=str(e),
            )
        
    def setup_recurring_payment(
            self, customer_data: CustomerData, payment_data: PaymentData
        ) -> PaymentResponse:
        stripe.api_key = os.getenv('STRIPE_API_KEY')
        price_id = os.getenv('STRIPE_PRICE_ID', '')
        try:
            customer = self._get_or_create_customer(customer_data) ## This method is private of class
            payment_method = self._attach_payment_method(
                customer.id, payment_data.source
            )

            self._set_default_payment_method(customer.id, payment_method.id)

            subscription = stripe.Subscription.create(
                customer=customer['id'],
                item = [
                    {'price' : price_id}
                ],
                expand=['latest_invoice.payment_intent']
            )

            print('Recurring payment setup succesful')
            amount = subscription['items']['data'][0]['price']['unit_amount']
            return PaymentResponse(
                status=subscription['status'],
                amount=amount,
                transaction_id=subscription['id'],
                message='Recurring payment setup succesful'
            )
        except StripeError as e:
            print(f'Failed: {e}')
            PaymentResponse(
                status='failed',
                amount=0,
                transaction_id=None,
                message=str(e)
            )

    def _get_or_create_customer(
            self, customer_data: CustomerData
    ) -> stripe.Customer:
        """
        Creates a new customer in Stripe or retrieves an existing one.
        """ 
        if customer_data.customer_id:
            customer = stripe.Customer.retrieve(customer_data.customer_id)
            print(f'Customer retrieved: {customer}')
        else:
            if not customer_data.contact_info.email:
                raise ValueError('Email required for subscription')
            customer = stripe.Customer.create(
                name= customer_data.name,
                email= customer_data.contact_info.email
            )
            print(f'Customer created: {customer.id}')
        return customer
    
    def _attach_payment_method(
            self, customer_id: str, payment_source: str
    ) -> stripe.PaymentMethod:
        """
        Attaches a payment method to a customer.
        """
        payment_method = stripe.PaymentMethod.retrieve(payment_source)
        stripe.PaymentMethod.attach(
            payment_method.id,
            customer=customer_id
        )
        print(f'Payment method {payment_method.id} attached to customer {customer_id}')
        return payment_method
    
    def _set_default_payment_method(
            self, customer_id: str, payment_method_id: str) -> None:
        """
        Sets the default payment method for a customer.
        """
        stripe.Customer.modify(
            customer_id,
            invoice_settings={
                "default_payment_method": payment_method_id,
            },
        )
        print(f"Default payment method set for customer {customer_id}")


class OfflinePaymentProcess(PaymentProcessor):
    def process_transaction(
        self, customer_data: CustomerData, payment_data: PaymentData
    ) -> PaymentResponse:
        print(f'Proccesing offline payment for {customer_data.name}')
        return PaymentResponse(
            status='succes',
            amount=payment_data.amount,
            transaction_id= str(uuid.uuid4()),
            message='Offline payment success'
        )
    
    """
    los siguientes métodos levantan errores porque no se pueden hacer reembolsos ni recurrencias a efectivo
    se incumple el principio de segregación de interfaces porque una clase no debería depender 
    de clases que no puede implementar
    """
    def refund_payment(self, transaction_id: str) -> PaymentResponse:
        print("refunds aren't supported in OfflinePaymentOricessor.")
        raise NotImplementedError("Refunds not supported in offline processor.")
    
    def setup_recurring_payment(self, customer_data: CustomerData, payment_data: PaymentData
    ) ->PaymentResponse:
        print("recurring payments aren't supported in OfflinePaymentOricessor.")
        raise NotImplementedError("Refunds not supported in offline processor.")   
    
class Notifier(Protocol):
    """
    Protocol for sending notifications.

    This protocol defines the interface for notifiers. Implementations
    should provide a method `send_confirmation` that sends a confirmation
    to the customer.
    """
    def send_confirmation(self, customer_data: CustomerData,): ...

class EmailNotifier(Notifier):
    def send_confirmation(self, customer_data: CustomerData):
        from email.mime.text import MIMEText

        if not customer_data.contact_info.email:
            print('Failed: missing email')
            raise ValueError('Email address is required')
        
        msg = MIMEText('Thank you for payment')
        msg['Subject'] = 'Payment confirmation'
        msg['From'] = "no-reply@example.com"
        msg['To'] = customer_data.contact_info.email

        print('Email send :)')

class SMSNotifier(Notifier):
    gateway : str

    def send_confirmation(self, customer_data: CustomerData):
        phone_number = customer_data.contact_info.phone

        if not phone_number:
            print('Phone is missing')
            return
        print(f'The message was sent to {phone_number} via {self.gateway} ')

class TransactionLooger:
    def log(self, customer_data: CustomerData, payment_data: PaymentData, payment_response: PaymentResponse ):
        with open('transaction.log','a') as log_file:
            log_file.write(f''' {customer_data.name} paid {payment_data.amount} succesfull\n
                                Payment status: {payment_response.status} ''')
            if payment_response.transaction_id:
                log_file.write(f''' Transaction ID: {payment_response.transaction_id}\n
                                    The message is: {payment_response.message}''')
    
    def log_refund(self, transaction_id: str, refund_response: PaymentResponse):
        with open('trasaction.log', 'a') as log_file:
            log_file.write(
                f"Refund processed for transaction {transaction_id}\n"
            )
            log_file.write(f"Refund status: {refund_response.status}\n")
            log_file.write(f"Message: {refund_response.message}\n")

class CustomerValidator:
    def validate(self, customer_data: CustomerData):
        if not customer_data.name:
            print("Invalid customer data: missing name")
            raise ValueError("Invalid customer data: missing name")
        if not customer_data.contact_info:
            print("Invalid customer data: missing contact info")
            raise ValueError("Invalid customer data: missing contact info")
        if not (
            customer_data.contact_info.email
            or customer_data.contact_info.phone
        ):
            print("Invalid customer data: missing email and phone")
            raise ValueError("Invalid customer data: missing email and phone")

class PaymentDataValidator:
    def validate(self, payment_data: PaymentData):
        if not payment_data.source:
            print("Invalid payment data: missing source")
            raise ValueError("Invalid payment data: missing source")
        if payment_data.amount <= 0:
            print("Invalid payment data: amount must be positive")
            raise ValueError("Invalid payment data: amount must be positive")
        
@dataclass
class PaymentService:
    payment_processor: PaymentProcessor
    notifier: Notifier
    customer_validator: CustomerValidator = field(
        default_factory=CustomerValidator
    )
    payment_validator: PaymentDataValidator = field(
        default_factory=PaymentDataValidator
    )
    logger: TransactionLooger = field(default_factory=TransactionLooger)

    def process_transaction(
        self, customer_data: CustomerData, payment_data: PaymentData
    ) -> PaymentResponse:
        self.customer_validator.validate(customer_data)
        self.payment_validator.validate(payment_data)
        payment_response = self.payment_processor.process_transaction(
            customer_data, payment_data
        )
        self.notifier.send_confirmation(customer_data)
        self.logger.log_transaction(
            customer_data, payment_data, payment_response
        )
        return payment_response

    def process_refund(self, transaction_id: str):
        refund_response = self.payment_processor.refund_payment(transaction_id)
        self.logger.log_refund(transaction_id, refund_response)
        return refund_response

    def setup_recurring(
        self, customer_data: CustomerData, payment_data: PaymentData
    ):
        recurring_response = self.payment_processor.setup_recurring_payment(
            customer_data, payment_data
        )
        self.logger.log_transaction(
            customer_data, payment_data, recurring_response
        )
        return recurring_response
    
if __name__ == '__main__':
    stripe_processor = StripePaymentProcessor()
    offline_processor = OfflinePaymentProcess()

    #Configuracion de la info del cliente

    customer_data_with_email = CustomerData(name="John Doe", contact_info=ContactInfo(email="john@gmail.com"))

    customer_data_with_phone = CustomerData(name="John Doe", contact_info=ContactInfo(phone="1234567890"))

    #Informacion del pago 
    payment_data = PaymentData(amount=100, source="tok_visa")

    # Notificadores
    email_notifier = EmailNotifier()

    sms_gateway = "YourSMSService"
    sms_notifier = SMSNotifier(sms_gateway)

     # # Usando el procesador con correo
    payment_service_email = PaymentService(stripe_processor, email_notifier)
    payment_service_email.process_transaction(customer_data_with_email, payment_data)

    # # Usando el procesador con el telefono
    payment_service_sms = PaymentService(stripe_processor, sms_notifier)
    sms_payment_response = payment_service_sms.process_transaction(customer_data_with_phone, payment_data)

    transaction_id_to_refund = sms_payment_response.transaction_id
    if transaction_id_to_refund:
        payment_service_email.process_refund(transaction_id_to_refund)

    # Using el procesador apagado con el email
    offline_payment_service = PaymentService(offline_processor, email_notifier)
    offline_payment_response = offline_payment_service.process_transaction(
        customer_data_with_email, payment_data
    )

    try:
        if offline_payment_response.transaction_id:
            offline_payment_service.process_refund(
                offline_payment_response.transaction_id
            )
    except Exception as e:
        print(f"Refund failed and PaymentService raised an exception: {e}")

    try:
        offline_payment_service.setup_recurring(
            customer_data_with_email, payment_data
        )

    except Exception as e:
        print(
            f"Recurring payment setup failed and PaymentService raised an exception {e}"
        )

    try:
        error_payment_data = PaymentData(amount=100, source="tok_radarBlock")
        payment_service_email.process_transaction(
            customer_data_with_email, error_payment_data
        )
    except Exception as e:
        print(f"Payment failed and PaymentService raised an exception: {e}")

    # Set up recurrence
    recurring_payment_data = PaymentData(amount=100, source="pm_card_visa")
    payment_service_email.setup_recurring(
        customer_data_with_email, recurring_payment_data
    )


