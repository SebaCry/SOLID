from typing import Protocol

from payment_service.commons import CustomerData

class NotifierProtocol(Protocol):
    """
    This protocol defines the interface for notifiers
    """

    def send_confirmation(self, customer_data:CustomerData):
        ...