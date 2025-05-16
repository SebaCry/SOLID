from abc import ABC, abstractmethod
from typing import Self, Optional
from dataclasses import dataclass
from commons import request 

class ChainHandler(ABC):
    _next_handlrer: Optional[Self]

    def set_next(self, handler: Self):
        self._next_handlrer = handler
        return handler
    
    @abstractmethod
    def handle(self, request):
        ...