from modbus_data_block import DataBlock
from modbus_static_functions import encode_float, decode_to_float, get_values_from_bytes, get_bytes_from_values

class ModbusSlaveContext():
    """This creates a modbus data model with each data access stored in a block."""

    __fx_mapper = {2: "d", 4: "i"}
    __fx_mapper.update([(i, "h") for i in (3, 6, 16)]) #22, 23
    __fx_mapper.update([(i, "c") for i in (1, 5, 15)])
    @classmethod
    def create(cls, **kwargs):
        return cls(**kwargs)

    def __init__(self, **kwargs):  # pylint: disable=unused-argument
        """Initialize the datastores.

        Defaults to fully populated
        sequential data blocks if none are passed in.

        :param kwargs: Each element is a ModbusDataBlock

            "di" - Discrete Inputs initializer
            "co" - Coils initializer
            "hr" - Holding Register initializer
            "ir" - Input Registers iniatializer
        """

        self.store = {}
        self.store["d"] = kwargs.get("di", DataBlock.create_empty())
        self.store["c"] = kwargs.get("co", DataBlock.create_empty())
        self.store["i"] = kwargs.get("ir", DataBlock.create_empty())
        self.store["h"] = kwargs.get("hr", DataBlock.create_empty())
        self.zero_mode = kwargs.get("zero_mode", True)
        self.changed = False
        #for key,val in self.store.items():
        #    print(f"{key}: {val}")

    def __str__(self):
        """Return a string representation of the context.

        :returns: A string representation of the context
        """
        return "Modbus Slave Context"

    def decode(self, fx):  # pylint: disable=invalid-name
        """Convert the function code to the datastore to.

        :param fx: The function we are working with
        :returns: one of [d(iscretes),i(nputs),h(olding),c(oils)
        """
        return self.__fx_mapper.get(fx, None)

    def reset(self):
        """Reset all the datastores to their default values."""
        for datastore in iter(self.store.values()):
            datastore.reset()

    def is_block_empty(self, fc_as_hex):
        block = self.store[self.decode(fc_as_hex)]
        if block.empty:
            return False
        return False

    def validate(self, fc_as_hex, address, count=1):
        """Validate the request to make sure it is in range.

        :param fc_as_hex: The function we are working with
        :param address: The starting address
        :param count: The number of values to test
        :returns: True if the request in within range, False otherwise
        """
        if not self.zero_mode:
            address = address + 1
        #txt = f"validate: fc-[{fc_as_hex}] address-{address}: count-{count}"
        #print(txt)
        #store_key = self.decode(fc_as_hex)
        #if store_key not in self.store.keys():
        #    return False
        block = self.store[self.decode(fc_as_hex)]
        return block.validate(address, count)

    def getValues(self, fc_as_hex, address, count=1):
        """Get `count` values from datastore.

        :param fc_as_hex: The function we are working with
        :param address: The starting address
        :param count: The number of values to retrieve
        :returns: The requested values from a:a+c
        """
        if not self.zero_mode:
            address = address + 1
        #txt = f"getValues: fc-[{fc_as_hex}] address-{address}: count-{count}"
        #_logger.debug(txt)
        return self.store[self.decode(fc_as_hex)].getValues(address, count)

    def setValues(self, fc_as_hex, address, values):
        """Set the datastore with the supplied values.

        :param fc_as_hex: The function we are working with
        :param address: The starting address
        :param values: The new values to be set
        """
        if not self.zero_mode:
            address = address + 1
        #txt = f"setValues[{fc_as_hex}] address-{address}: count-{len(values)}"
        #_logger.debug(txt)
        self.store[self.decode(fc_as_hex)].setValues(address, values)

    def register(self, function_code, fc_as_hex, datablock=None):
        """Register a datablock with the slave context.

        :param function_code: function code (int)
        :param fc_as_hex: string representation of function code (e.g "cf" )
        :param datablock: datablock to associate with this function code
        """
        self.store[fc_as_hex] = datablock or DataBlock.create()
        self.__fx_mapper[function_code] = fc_as_hex