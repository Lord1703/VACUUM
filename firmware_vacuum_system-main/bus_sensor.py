import time
from entity import IntEntity, FloatEntity
from parameters import VacuumErrors, VP, I2C_RETRIES, BMP280_NO_DATA_AVAILABLE
from machine import I2C, Pin


class Bus:
    """Класс переключения мультиплексора."""
    def __init__(self, i2c_bus, address=0x70):
        self.__i2c_bus = i2c_bus
        self.__address = address
        self.__active_sensor = -1

    def switch_to_sensor(self, bus):
        if self.__active_sensor == bus:
            return True
        value = 1 << bus
        for retry_num in range(I2C_RETRIES):
            write_result = self.__i2c_bus.writeto(self.__address, value.to_bytes(1,'big'))
            if not write_result:
                print(f'Not switched on try {retry_num}')
                if retry_num == I2C_RETRIES - 1:
                    print('Switch bus error')
                    return False
        self.__active_sensor = bus
        return True


class BusSensor:
    """Класс для считывания показаний с датчика давления."""
    def __init__(self, bus, bus_number, sensor, store, samples=64, error_store_num=0, pressure_store_num=0):
        self.__bus = bus
        self.__bus_number = bus_number
        self.__samples = samples
        self.__sensor = sensor
        self.error = IntEntity(error_store_num, 0, store)
        self.pressure = FloatEntity(pressure_store_num, float(0), store)
        self.last_update_time = 0
        self.initialize()

    def initialize(self):
        if not self.__bus.switch_to_sensor(self.__bus_number):
            self.error.set_value(VacuumErrors.SwitchBusError)
            return
        for retry_num in range(I2C_RETRIES):
            try:
                self.__sensor.initialize()
                break
            except:
                print(f'Sensor init error on try {retry_num}')
                if retry_num == I2C_RETRIES - 1:
                    print('Init sensor error')
                    self.error.set_value(VacuumErrors.InitSensorError)
                    return
        self.error.set_value(VacuumErrors.NoError)

    def update_pressure(self):
        if not self.__bus.switch_to_sensor(self.__bus_number):
            self.error.set_value(VacuumErrors.SwitchBusError)
            return
        old_val = self.pressure.value
        for retry_num in range(I2C_RETRIES):
            try:
                new_val = self.__sensor.pressure
                break
            except Exception as e:
                print(f'Read pressure error on try {retry_num}: {str(e)}')
                if retry_num == I2C_RETRIES - 1:
                    self.error.set_value(VacuumErrors.InitSensorError)
                    return
        # Проверка на подвисание показаний давления
        if old_val != new_val and new_val != BMP280_NO_DATA_AVAILABLE:
            self.pressure.set_value(new_val)
            self.last_update_time = time.ticks_ms()
        else:
            self.check_time_error()
            return
        self.error.set_value(VacuumErrors.NoError)

    def check_time_error(self):
        interval = time.ticks_diff(time.ticks_ms(), self.last_update_time)
        #если время нормального обновления больше заданного интервала - ошибка
        if interval >= VP.pressure_update_critical_time:
            self.error.set_value(VacuumErrors.UpdateTimeError)
        else:
            self.error.set_value(VacuumErrors.NoError)
