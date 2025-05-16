from .listener import Listener
from dataclasses import dataclass, field

class ListenersManager[T]:
    listeners = list[Listener] = field(default_factory=list)

    def subscribe(self, listener: Listener):
        self.listeners.append(listener)

    def unsubcribe(self, listener: Listener):
        self.listeners.remove(listener)

    def notify_all(self, event: T):
        for listener in self.listeners:
            listener.notify(event)