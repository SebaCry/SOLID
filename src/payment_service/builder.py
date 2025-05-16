from dataclasses import dataclass
from typing import Optional, Self

from service import PaymentService
from commons import PaymentData, CustomerData
from notifiers import EmailNotifier, SMSNotifier
from factory import PaymentProcessorFactory
from .loggers import TransactionLogger
from .notifiers import NotifierProtocol
from .processors import (
    PaymentProcessorProtocol,
    RecurringPaymentProcessorProtocol,
    RefundProcessorProtocol,
)
from .validators import CustomerValidator, PaymentDataValidator, ChainHandler, CustomerHandler
from listeners import ListenersManager, AccountAbilityListener

@dataclass
class PaymentServiceBuilder():

    payment_processor: Optional [PaymentProcessorProtocol] = None
    notifier: Optional [NotifierProtocol] = None
    validators: Optional [ChainHandler] = None
    logger: Optional [TransactionLogger] = None
    listener: Optional [ListenersManager] = None
    refund_processor: Optional[RefundProcessorProtocol] = None
    recurring_processor: Optional[RecurringPaymentProcessorProtocol] = None

    def set_logger(self) -> Self:
        self.logger = TransactionLogger()
        return self
    
    # def set_payment_validator(self) -> Self:
    #     self.payment_validator = PaymentDataValidator()
    #     return self
    
    # def set_customer_validator(self) -> Self: 
    #     self.customer_validator = CustomerValidator()
    #     return self

    def set_chain_of_validations(self):
        customer_handler = CustomerHandler()
        customer_handler_2 = CustomerHandler()
        customer_handler.set_next(customer_handler_2)
    
    def set_payment_processor(self, payment_data: PaymentData) -> Self:
        self.payment_processor = PaymentProcessorFactory.create_payment_processor(payment_data)
        return self
    
    def set_notifier(self, customer_data: CustomerData) -> Self:
        if customer_data.contact_info.email:
            self.notifier = EmailNotifier()
        if customer_data.contact_info.phone:
            self.notifier = SMSNotifier(gateway='MyCustomGateway')

    def build(self):
        if not all(
            [
                self.payment_processor,
                self.notifier,
                self.validators,
                self.logger,
                self.listener   
            ]
        ):
            missing = [
                name
                for name, value in [
                    ('process_processor', self.payment_processor),
                    ('notifier', self.notifier),
                    ('validators', self.validators)
                    ('logger', self.logger),
                    ('listener', self.listener)
                ]

                if value is None
            ]
            raise ValueError(f"Missing {missing}")
        
        return PaymentService(
            payment_processor=self.payment_processor,
            notifier=self.notifier,
            validators=self.validators,
            logger=self.logger,
            listeners=self.listener
        )
    
    def set_list(self):
        listener = ListenersManager()

        accountability_listener = AccountAbilityListener()
        listener.subscribe(accountability_listener)

        self.listener = listener