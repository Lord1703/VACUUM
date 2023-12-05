from modbus_exceptions import RegisterAddressException, ValueTypeException
from base_entity import IEntity, SyncEntity
from modbus_static_functions import decode_to_float, encode_float, get_bytes_from_values, get_values_from_bytes

class ArrayEntity(IEntity):
    def __init__(self, register, value, store, code=3):
        value_length = len(value)
        if not store.validate(code, register, value_length):
            raise RegisterAddressException(f"[ code : {code} | register : {register} | value : {value} | value_length: {value_length} | type : {str(type(value))} ]")
        if not isinstance(value, list):
            raise ValueTypeException(f"Expected type list [ code : {code} | register : {register} | value : {value} | type : {str(type(value))} ]")
        super().__init__(code, register, store, value_length)
        self.set_value(value)

    def set_value(self, new_value):
        if not isinstance(new_value, list):
            return False
        if len(new_value) != self.value_length:
            return False
        if self.value != new_value:
            self.value = new_value
            self.set_to_store(new_value)
            return True
        return False

    def get_value(self):
        self.value = self.get_from_store()
        return self.value.copy()

class IntEntity(IEntity):
    def __init__(self, register, value, store, code=3):
        if not store.validate(code, register, 1):
            raise RegisterAddressException(f"[ code : {code} | register : {register} | value : {value} | type : {str(type(value))} ]")
        if not isinstance(value, int):
            raise ValueTypeException(f"Expected type int [ code : {code} | register : {register} | value : {value} | type : {str(type(value))} ]")
        super().__init__(code, register, store, 1)
        self.set_value(value)

    def set_value(self, new_value):
        if not isinstance(new_value, int):
            return False
        if self.value != new_value:
            self.value = new_value
            self.set_to_store(new_value)
            return True
        return False

    def get_value(self):
        """ Считать данные из регистра и вернуть."""
        new_value = self.get_from_store()[0]
        if self.value != new_value:
            self.value = new_value
            #print(f"New int value: {str(self.value)}")
        return self.value

    def increment(self):
        self.set_value(self.value + 1)

class FloatEntity(IEntity):
    def __init__(self, register, value, store, code=3):
        if not store.validate(code, register, 2):
            raise RegisterAddressException(f"[ code : {code} | register : {register} | value : {value} | type : {str(type(value))} ]")
        if not isinstance(value, float):
            raise ValueTypeException(f"Expected type float [ code : {code} | register : {register} | value : {value} | type : {str(type(value))} ]")
        super().__init__(code, register, store, 2)
        self.set_value(value)

    def set_value(self, new_value):
        if not isinstance(new_value, float):
            return False
        if self.value != new_value:
            self.value = new_value
            ar = encode_float(new_value)
            val_to_write = get_values_from_bytes(ar)
            self.set_to_store(val_to_write)
            return True
        return False

    def get_value(self, num_of_dec=4):
        values = self.get_from_store()
        array_value = get_bytes_from_values(values)
        result = decode_to_float(array_value)
        if num_of_dec > 0:
            self.value = round(result, num_of_dec)
        else:
            self.value = result
        return self.value