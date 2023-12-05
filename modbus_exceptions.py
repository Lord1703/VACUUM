class ModbusException(Exception):
    """Base modbus exception."""

    def __init__(self, string):
        """Initialize the exception.

        :param string: The message to append to the error
        """
        self.string = string
        super().__init__()

    def __str__(self):
        """Return string representation."""
        return f"Modbus Error: {self.string}"

    def isError(self):  # pylint: disable=invalid-name
        """Error"""
        return True

class ParameterException(ModbusException):
    """Error resulting from invalid parameter."""

    def __init__(self, string=""):
        """Initialize the exception.

        :param string: The message to append to the error
        """
        message = f"[Invalid Parameter] {string}"
        ModbusException.__init__(self, message)

class ValueTypeException(ModbusException):
    def __init__(self, string=""):
        message = f"[Wrong value type] {string}"
        ModbusException.__init__(self, message)

class RegisterAddressException(ModbusException):
    def __init__(self, string=""):
        message = f"[Wrong address or registers count] {string}"
        ModbusException.__init__(self, message)
