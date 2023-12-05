import sys
import time
import _thread

from machine import Pin, I2C, UART
from modbus_data_block import DataBlock
from modbus_rtu_slave_rs485 import ModbusRtuSlaveRS485
from parameters import I2C_FREQ, I2C_NUM, I2C_SCL, I2C_SDA
from vacuumator import Vacuumator3000

uart0 = UART(0, baudrate=115200, tx=Pin(0), rx=Pin(1), bits=8, parity=None, stop=1)
modbus_slave = ModbusRtuSlaveRS485(uart0, 1, False, dir_pin=4, hr=DataBlock({0: [0]*31}))
value_store = modbus_slave.get_context()

i2c = I2C(I2C_NUM, sda=Pin(I2C_SDA), scl=Pin(I2C_SCL), freq=I2C_FREQ)
vacuumator = Vacuumator3000(i2c, value_store)

second_continue = True
sync = _thread.allocate_lock()


def second_thread(second_continue, vacuumator):
    try:
        print("Second thread started")
        while second_continue:
            vacuumator.tact()
    except BaseException as err:
        sys.print_exception(err)
    finally:
        print("Second thread stoped")

bufferSTDINthread = _thread.start_new_thread(
    second_thread, (second_continue, vacuumator))

try:
    while True:
        modbus_slave.receive()
        if value_store.changed:
            vacuumator.update_store_values()
            value_store.changed = False
        time.sleep(.0001)
except KeyboardInterrupt:
    print("Keyboard EXIT")
finally:
    second_continue = False
    time.sleep(.1)
    print("System STOPED")