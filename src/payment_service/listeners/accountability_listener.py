from .listener import Listener

class AccountAbilityListener[T](Listener):
    def notify(self, event: T):
        print(f"Notificando el evento {event}")