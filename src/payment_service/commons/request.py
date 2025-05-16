from .payment_data import PaymentData
from .customer import CustomerData
from pydantic import BaseModel


class Request(BaseModel):
    customer_data: CustomerData
    payment_data: PaymentData  
    
