from modbus_static_functions import check_crc, crc16, pack_bitstring, unpack_bitstring, get_values_from_bytes, get_bytes_from_values
from modbus_constants import ModbusErrorCodes

functions = [0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x0F, 0x10]
allowed_functions = [0x03, 0x06, 0x10]

class ModbusFrameBase:
    def __init__(self, device_addr=1, func_code=0):
        self.device_addr = device_addr
        self.func_code = func_code

    def execute(self, context):
        """Override in derived Class"""
        pass

    def get_frame(self):
        """Override in derived Class"""
        pass

    def get_error_frame(self, error_code):
        return ModbusErrorFrame(device_addr=self.device_addr, func_code=self.func_code, error_code=error_code).get_frame()

    @staticmethod
    def parse_frame(frame, context):
        device_addr = frame[0]
        func_code = frame[1]
        register = (frame[2]<<8) + frame[3]
        count_or_data = (frame[4]<<8) + frame[5]
        data = None
        bc = None
        if func_code in [0x0F, 0x10]:
            bc = frame[6]
            data = frame[7:7+bc]
        if context.is_block_empty(func_code):
            return ModbusErrorFrame(device_addr=device_addr, func_code=func_code, error_code=ModbusErrorCodes.AddressIsNotAvailabe)
        if func_code == 1:
            return ReadCoilsFrame(device_addr=device_addr, register=register, count=count_or_data)
        elif func_code == 2:
            return ReadDiscreteInputsFrame(device_addr=device_addr, register=register, count=count_or_data)
        elif func_code == 3:
            return ReadHoldingRegistersFrame(device_addr=device_addr, register=register, count=count_or_data)
        elif func_code == 4:
            return ReadInputRegistersFrame(device_addr=device_addr, register=register, count=count_or_data)
        elif func_code == 5:
            return WriteSingleCoilFrame(device_addr=device_addr, register=register, data=count_or_data)
        elif func_code == 6:
            return WriteSingleRegisterFrame(device_addr=device_addr, register=register, data=count_or_data)
        elif func_code == 15:
            return WriteMultipleCoilsFrame(device_addr=device_addr, register=register, count=count_or_data, byte_count=bc, data=data)
        elif func_code == 16:
            return WriteMultipleRegistersFrame(device_addr=device_addr, register=register, count=count_or_data, byte_count=bc, data=data)
        else:
            return ModbusErrorFrame(device_addr=device_addr, func_code=func_code, error_code=ModbusErrorCodes.FuncCodeCanNotBeHandle)

class ModbusErrorFrame(ModbusFrameBase):
    def __init__(self, device_addr=0, func_code=0, error_code=None):
        func_code |= (1 << 7)
        super().__init__(device_addr, func_code)
        self.error_code = error_code

    def get_frame(self):
        response = bytearray([self.device_addr])
        response += bytearray([self.func_code])
        response += bytearray([self.error_code])
        crc = crc16(response)
        response += bytearray([crc&0xFF, crc>>8])
        return response

    def execute(self, context):
        return self.get_frame()

"""READ FRAMES"""

class ModbusReadFrame(ModbusFrameBase):
    def __init__(self, device_addr=1, func_code=0, register=0, count=1):
        super().__init__(device_addr=device_addr, func_code=func_code)
        self.register = register
        self.count = count

    def get_frame(self, values):
        response = bytearray([self.device_addr])
        response += bytearray([self.func_code])
        response += bytearray([len(values)])
        response += bytearray(values)
        crc = crc16(response)
        response += bytearray([crc&0xFF, crc>>8])
        return response

class ReadCoilsFrame(ModbusReadFrame):
    def __init__(self, device_addr=1, register=0, count=1):
        func_code = 1
        super().__init__(device_addr=device_addr, func_code=func_code, register=register, count=count)

    def execute(self, context):
        if not context.validate(self.func_code, self.register, self.count):
            return self.get_error_frame(ModbusErrorCodes.AddressIsNotAvailabe)
        values = context.getValues(self.func_code, self.register, self.count)
        return self.get_frame(pack_bitstring(values))

class ReadDiscreteInputsFrame(ModbusReadFrame):
    def __init__(self, device_addr=1, register=0, count=1):
        func_code = 2
        super().__init__(device_addr=device_addr, func_code=func_code, register=register, count=count)

    def execute(self, context):
        if not context.validate(self.func_code, self.register, self.count):
            return self.get_error_frame(ModbusErrorCodes.AddressIsNotAvailabe)
        values = context.getValues(self.func_code, self.register, self.count)
        return self.get_frame(pack_bitstring(values))

class ReadHoldingRegistersFrame(ModbusReadFrame):
    def __init__(self, device_addr=1, register=0, count=1):
        func_code = 3
        super().__init__(device_addr=device_addr, func_code=func_code, register=register, count=count)

    def execute(self, context):
        if not context.validate(self.func_code, self.register, self.count):
            return self.get_error_frame(ModbusErrorCodes.AddressIsNotAvailabe)
        values = context.getValues(self.func_code, self.register, self.count)
        return self.get_frame(get_bytes_from_values(values))

class ReadInputRegistersFrame(ModbusReadFrame):
    def __init__(self, device_addr=1, register=0, count=1):
        func_code = 4
        super().__init__(device_addr=device_addr, func_code=func_code, register=register, count=count)

    def execute(self, context):
        if not context.validate(self.func_code, self.register, self.count):
            return self.get_error_frame(ModbusErrorCodes.AddressIsNotAvailabe)
        values = context.getValues(self.func_code, self.register, self.count)
        return self.get_frame(get_bytes_from_values(values))

"""WRITE FRAMES"""

class ModbusWriteFrame(ModbusFrameBase):
    def __init__(self, device_addr=1, func_code=0, register=0, data=None):
        super().__init__(device_addr=device_addr, func_code=func_code)
        self.register = register
        self.data = data

class ModbusWriteSingleFrame(ModbusWriteFrame):
    def __init__(self, device_addr=1, func_code=0, register=0, data=None):
        super().__init__(device_addr=device_addr, func_code=func_code, register=register, data=data)

    def get_frame(self, values):
        response = bytearray([self.device_addr])
        response += bytearray([self.func_code])
        response += bytearray([self.register>>8, self.register&0xFF])
        response += bytearray(values)
        crc = crc16(response)
        response += bytearray([crc&0xFF, crc>>8])
        return response

class ModbusWriteMultipleFrame(ModbusWriteFrame):
    def __init__(self, device_addr=1, func_code=0, register=0, count=1, byte_count=1, data=None):
        super().__init__(device_addr=device_addr, func_code=func_code, register=register, data=data)
        self.count = count
        self.byte_count = byte_count

    def get_frame(self):
        response = bytearray([self.device_addr])
        response += bytearray([self.func_code])
        response += bytearray([self.register>>8, self.register&0xFF])
        response += bytearray([self.count>>8, self.count&0xFF])
        crc = crc16(response)
        #print(f"{response} : {crc} : {hex(crc&0xFF)}, {hex(crc>>8)}")
        response += bytearray([crc&0xFF, crc>>8])
        return response

class WriteSingleCoilFrame(ModbusWriteSingleFrame):
    def __init__(self, device_addr=1, register=0, data=None):
        func_code = 5
        super().__init__(device_addr=device_addr, func_code=func_code, register=register, data=data)

    def execute(self, context):
        if not context.validate(self.func_code, self.register, 1):
            return self.get_error_frame(ModbusErrorCodes.AddressIsNotAvailabe)
        #context.setValues(self.func_code, self.register, unpack_bitstring(self.data))
        context.setValues(self.func_code, self.register, self.data > 0)
        values = context.getValues(self.func_code, self.register, 1)
        return self.get_frame(pack_bitstring(values))

class WriteSingleRegisterFrame(ModbusWriteSingleFrame):
    def __init__(self, device_addr=1, register=0, data=None):
        func_code = 6
        super().__init__(device_addr=device_addr, func_code=func_code, register=register, data=data)

    def execute(self, context):
        if not context.validate(self.func_code, self.register, 1):
            return self.get_error_frame(ModbusErrorCodes.AddressIsNotAvailabe)
        #context.setValues(self.func_code, self.register, get_values_from_bytes(self.data))
        context.setValues(self.func_code, self.register, self.data)
        values = context.getValues(self.func_code, self.register, 1)
        context.changed = True
        return self.get_frame(get_bytes_from_values(values))

class WriteMultipleCoilsFrame(ModbusWriteMultipleFrame):
    def __init__(self, device_addr=1, register=0, count=1, byte_count=1, data=None):
        func_code = 15
        super().__init__(device_addr=device_addr, func_code=func_code, register=register, count=count, byte_count=byte_count, data=data)
        self.count = count
        self.byte_count = byte_count

    def execute(self, context):
        if not context.validate(self.func_code, self.register, self.count):
            return self.get_error_frame(ModbusErrorCodes.AddressIsNotAvailabe)
        context.setValues(self.func_code, self.register, unpack_bitstring(self.data))
        #values = context.getValues(self.func_code, self.register, self.count)
        return self.get_frame()

class WriteMultipleRegistersFrame(ModbusWriteMultipleFrame):
    def __init__(self, device_addr=1, register=0, count=1, byte_count=1, data=None):
        func_code = 16
        super().__init__(device_addr=device_addr, func_code=func_code, register=register, count=count, byte_count=byte_count, data=data)

    def execute(self, context):
        if not context.validate(self.func_code, self.register, self.count):
            return self.get_error_frame(ModbusErrorCodes.AddressIsNotAvailabe)
        context.setValues(self.func_code, self.register, get_values_from_bytes(self.data))
        #values = context.getValues(self.func_code, self.register, self.count)
        context.changed = True
        return self.get_frame()