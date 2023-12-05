from modbus_exceptions import ParameterException

class DataBlock:
    def __init__(self, values=None, mutable=True, empty=False):
        self.empty = empty
        self.values = {}
        self._process_values(values)
        self.mutable = mutable
        self.default_value = self.values.copy()
        self.address = next(iter(self.values.keys()))

    @classmethod
    def create(cls):
        return cls([0x00] * 65536)

    @classmethod
    def create_empty(cls):
        return cls({-1: 0}, empty=True)

    def __iter__(self):
        if isinstance(self.values, dict):
            return iter(self.values.items())
        return enumerate(self.values, self.address)

    def __str__(self):
        return str(self.values)

    def default(self, count, value=False):
        self.default_value = value
        self.values = [self.default_value] * count
        self.address = 0x00

    def reset(self):
        self.values = self.default_value.copy()

    def validate(self, address, count=1):
        if not count:
            return False
        handle = set(range(address, address + count))
        return handle.issubset(set(iter(self.values.keys())))

    def getValues(self, address, count=1):
        return [self.values[i] for i in range(address, address + count)]

    def setValues(self, address, values, use_as_default=False):
        if isinstance(values, dict):
            new_offsets = list(set(values.keys()) - set(self.values.keys()))
            if new_offsets and not self.mutable:
                raise ParameterException(f"Offsets {new_offsets} not in range")
            self._process_values(values)
        else:
            if not isinstance(values, list):
                values = [values]
            for idx, val in enumerate(values):
                if address + idx not in self.values and not self.mutable:
                    raise ParameterException("Offset {address+idx} not in range")
                self.values[address + idx] = val
        if not self.address:
            self.address = next(iter(self.values.keys()))
        if use_as_default:
            for idx, val in iter(self.values.items()):
                self.default_value[idx] = val

    def _process_values(self, values):
        print(values)
        def _process_as_dict(values):
            for idx, val in iter(values.items()):
                if isinstance(val, (list, tuple)):
                    for i, v_item in enumerate(val):
                        self.values[idx + i] = v_item
                else:
                    self.values[idx] = int(val)

        if isinstance(values, dict):
            _process_as_dict(values)
            return
        #if hasattr(values, "__iter__"):
        if isinstance(values, list):
            values = dict(enumerate(values))
        elif values is None:
            values = {}
        else:
            raise ParameterException("Values for datastore must be a list or dictionary")
        _process_as_dict(values)