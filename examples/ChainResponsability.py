from typing import Protocol

class Validator(Protocol):
    def validate(self, value: int):
        pass

    def set_next(self, data):
        pass

class MontoValidator(Validator):
    def validate(self, value):
        if value['monto'] < 1000:
            return True
        return False
    
class TarjetaValidator(Validator):
    def validate(self, value):
        if value['tarjeta'] == 'VISA':
            return True
        return False
    

class FraudeValidator(Validator):
    def validate(self, value):
        return not value.get("fraude", False)
    
monto_validator = MontoValidator()
tarjeta_validator = TarjetaValidator()
fraude_validator = FraudeValidator()

monto_validator.set_next(tarjeta_validator)
tarjeta_validator.set_next(fraude_validator)

solicitud = {"monto": 500, "tarjeta": "VISA", "fraude": False}

if not monto_validator.validate(solicitud):
    raise ValueError(f"La solicitud no es válida: {solicitud}")
print("Solicitud válida")
