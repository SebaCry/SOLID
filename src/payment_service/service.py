from dataclasses import dataclass
from typing import Optional, Self

from .commons import CustomerData, PaymentData, PaymentResponse
from .loggers import TransactionLogger
from .notifiers import NotifierProtocol
from .processors import (
    PaymentProcessorProtocol,
    RecurringPaymentProcessorProtocol,
    RefundProcessorProtocol,
)
from .validators import CustomerValidator, PaymentDataValidator
from factory import PaymentProcessorFactory


@dataclass
class PaymentService:
    """
    Servicio principal para procesar pagos con diferentes procesadores de pago.
    
    Esta clase implementa el patrón de inyección de dependencias, recibiendo todos
    los componentes necesarios a través del constructor.
    
    Attributes:
        payment_processor: Procesador de pagos principal
        notifier: Servicio para enviar notificaciones
        customer_validator: Validador de datos del cliente
        payment_validator: Validador de datos de pago
        logger: Registrador de transacciones
        refund_processor: Procesador de reembolsos (opcional)
        recurring_processor: Procesador de pagos recurrentes (opcional)
    """
    payment_processor: PaymentProcessorProtocol
    notifier: NotifierProtocol
    customer_validator: CustomerValidator
    payment_validator: PaymentDataValidator
    logger: TransactionLogger
    refund_processor: Optional[RefundProcessorProtocol] = None
    recurring_processor: Optional[RecurringPaymentProcessorProtocol] = None

    @classmethod
    def create_with_payment_processor(cls, payment_data: PaymentData, **kwargs) -> Self:
        """
        Método de clase (factory) que crea una instancia de PaymentService con el procesador adecuado.
        
        Este método utiliza el patrón Factory para determinar y crear el procesador de pagos
        adecuado según los datos de pago proporcionados, simplificando la creación de instancias
        de PaymentService.
        
        Args:
            cls: La clase PaymentService (proporcionada automáticamente por @classmethod)
            payment_data: Datos del pago que determinan qué procesador usar
            **kwargs: Argumentos adicionales para el constructor de PaymentService
                     (notifier, validators, logger, etc.)
        
        Returns:
            Una nueva instancia de PaymentService configurada con el procesador adecuado
            
        Raises:
            ValueError: Si no se puede crear un procesador para los datos de pago proporcionados
        """
        try:
            processor = PaymentProcessorFactory.create_payment_processor(
                payment_data
            )
            return cls(
                payment_processor=processor,
                **kwargs 
            )
        except ValueError as e:
            print(f"Error creating payment service: {e}")
            raise e

    def set_notifier(self, notifier: NotifierProtocol):
        """
        Cambia el notificador utilizado por el servicio.
        
        Permite modificar dinámicamente el componente de notificación sin crear
        una nueva instancia del servicio.
        
        Args:
            notifier: El nuevo notificador a utilizar
        """
        print("Changing the notifier implementation")
        self.notifier = notifier

    def process_transaction(
        self, customer_data: CustomerData, payment_data: PaymentData
    ) -> PaymentResponse:
        """
        Procesa una transacción de pago completa.
        
        Este método orquesta todo el flujo de procesamiento de pagos:
        1. Valida los datos del cliente y del pago
        2. Procesa la transacción con el procesador de pagos
        3. Envía una notificación de confirmación
        4. Registra la transacción
        
        Args:
            customer_data: Datos del cliente que realiza el pago
            payment_data: Datos del pago a procesar
            
        Returns:
            La respuesta del procesador de pagos
        """
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
        """
        Procesa un reembolso para una transacción existente.
        
        Este método utiliza el procesador de reembolsos opcional para devolver
        un pago previamente realizado.
        
        Args:
            transaction_id: Identificador de la transacción a reembolsar
            
        Returns:
            La respuesta del procesador de reembolsos
            
        Raises:
            Exception: Si este servicio no tiene configurado un procesador de reembolsos
        """
        if not self.refund_processor:
            raise Exception("this processor does not support refunds")
        refund_response = self.refund_processor.refund_payment(transaction_id)
        self.logger.log_refund(transaction_id, refund_response)
        return refund_response

    def setup_recurring(
        self, customer_data: CustomerData, payment_data: PaymentData
    ):
        """
        Configura un pago recurrente para un cliente.
        
        Este método utiliza el procesador de pagos recurrentes opcional para
        establecer un plan de pagos periódicos.
        
        Args:
            customer_data: Datos del cliente para el pago recurrente
            payment_data: Datos del pago recurrente a configurar
            
        Returns:
            La respuesta del procesador de pagos recurrentes
            
        Raises:
            Exception: Si este servicio no tiene configurado un procesador de pagos recurrentes
        """
        if not self.recurring_processor:
            raise Exception("this processor does not support recurring")
        recurring_response = self.recurring_processor.setup_recurring_payment(
            customer_data, payment_data
        )
        self.logger.log_transaction(
            customer_data, payment_data, recurring_response
        )
        return recurring_response