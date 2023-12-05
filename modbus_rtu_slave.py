import time
from modbus_frames import ModbusFrameBase, ModbusErrorFrame
from modbus_context import ModbusSlaveContext
from modbus_static_functions import check_crc

class ModbusRtuMessageHandler:
    def __init__(self, device_addr=1, debug=True, **kwargs):
        self.device_addr = device_addr
        self.context = ModbusSlaveContext.create(**kwargs)
        self.debug = debug

    def handle_message(self, frame):
        received_message = ModbusFrameBase.parse_frame(frame, self.context)
        result = received_message.execute(self.context)
        return result

class ModbusRtuSlave:
    def __init__(self, uart, device_addr, debug, **kwargs):
        self.device_addr = device_addr
        self.uart = uart
        self.handler = ModbusRtuMessageHandler(device_addr=device_addr, **kwargs)
        self.debug = debug
        self.stopped = False
        self.frame = []
        self.error = 0

    def stop(self):
        self.stopped = True

    def get_context(self):
        return self.handler.context

    def run(self):
        try:
            if self.debug: print("Modbus: ModbusRtuSlaveCustom started")
            self.uart.read() #clear buffer
            while not self.stopped:
                receive()
                time.sleep(0.001)
        except BaseException as er:
            self.error = 1

    def receive(self):
        if self.uart.any():
            r_byte = self.uart.readline()
            self.frame += r_byte
            if self.check_received():
                if self.debug: print(f"Modbus: Frame received: {self.frame}")
                responce = self.handler.handle_message(self.frame)
                self.frame = []
                if responce is not None:
                    self.send_answer(responce)

    def send_answer(self, responce):
        if self.debug: print(f"Modbus: Answer: {responce}")
        self.uart.write(responce)

    def check_received(self):
        length = len(self.frame)
        if length == 0:
            if self.debug: print(f"Modbus: Frame is empty!")
            return False
        if self.frame[0] != self.device_addr:
            if self.debug: print(f"Modbus: Wrong address: {self.frame}! Clear frame")
            self.frame = []
            return False
        if length < 8:
            if self.debug: print(f"Modbus: Part of message received: {self.frame}! Wait another")
            return False
        if self.frame[1] in [15, 16]:
            data_count = self.frame[6]
            full_count = 9 + data_count
            if length < full_count:
                if self.debug: print(f"Modbus: Part of message received: {self.frame}! Wait another")
                return False
            frame = self.frame[0:full_count]
        else:
            frame = self.frame[0:9]
        if not check_crc(frame):
            if self.debug: print(f"Modbus: Bad crc: {frame}! Clear frame")
            self.frame = []
            return False
        return True