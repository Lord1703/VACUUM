from machine import Pin
import time
from modbus_frames import functions
from modbus_rtu_slave import ModbusRtuSlave
from modbus_static_functions import check_crc

class ModbusRtuSlaveRS485(ModbusRtuSlave):
    def __init__(self, uart, device_addr, debug, **kwargs):
        super().__init__(uart, device_addr, debug, **kwargs)
        self.dir_pin = Pin(kwargs.get("dir_pin"), Pin.OUT)
        self.dir_pin.low()
        self.baudrate = kwargs.get("baudrate", 115200)
        if self.baudrate > 19200:
            #self.silent_interval = 1.75 / 1000  # ms
            self.silent_interval = 0.007
        else:
            self._t0 = float((1 + 8 + 2)) / self.baudrate
            self.inter_char_timeout = 1.5 * self._t0
            self.silent_interval = 3.5 * self._t0
        self.silent_interval = round(self.silent_interval, 6)
        if self.debug: print(f"Modbus: silent_interval: {self.silent_interval}")

    def send_answer(self, responce):
        if self.debug: print(f"Modbus: Answer (rs485): {responce}")
        self.dir_pin.high()
        #time.sleep(self.silent_interval)
        self.uart.write(responce)
        time.sleep(self.silent_interval)
        self.dir_pin.low()