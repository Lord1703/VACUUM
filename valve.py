from machine import Pin
from entity import IntEntity
import time

'''
Класс клапана
Запоминает состояние и время его последнего изменения
'''
class Valve:
    def __init__(self, pin_num, store, state_store_num=0):
        self.pin =  Pin(pin_num, Pin.OUT)
        self.pin.low()
        self.is_open = IntEntity(state_store_num, 0, store)
        self.last_time_change = 0

    def open(self):
        if self.is_open.value == 1:
            return
        self.pin.high()
        self.is_open.set_value(1)
        self.last_time_change = time.ticks_ms()

    def close(self):
        if self.is_open.value == 0:
            return
        self.pin.low()
        self.is_open.set_value(0)
        self.last_time_change = time.ticks_ms()

    def toggle(self):
        if self.is_open.value == 1:
            self.close()
        else:
            self.open()

'''
Клапан ресивера
Считает процент времени в открытом состоянии (а это работа мотора)
относительно всего времени работы системы. Пересчитывается постоянно
в основном такте ресивера
'''
class ReceiverValve(Valve):
    def __init__(self, pin_num, store, state_store_num=0, pump_work_percent_store_num=0):
        super().__init__(pin_num, store, state_store_num=state_store_num)
        self.start_time = 0
        self.stop_time = 0
        self.full_work_time = 0
        self.percent = IntEntity(pump_work_percent_store_num, 0, store)

    def open(self):
        if self.is_open.value == 1:
            return
        self.pin.high()
        self.is_open.set_value(1)
        self.last_time_change = time.ticks_ms()
        self.start_time = self.last_time_change

    def close(self):
        if self.is_open.value == 0:
            return
        self.pin.low()
        self.is_open.set_value(0)
        self.last_time_change = time.ticks_ms()
        self.stop_time = self.last_time_change

    def calc_percent(self):
        if self.is_open.value:
            time_now = time.ticks_ms()
            work_time = time_now - self.start_time
            self.start_time = time_now
        else:
            work_time = self.stop_time - self.start_time
            self.start_time = 0
            self.stop_time = 0
        self.full_work_time += work_time
        self.percent.set_value(int(self.full_work_time * 100 / time.ticks_ms()))