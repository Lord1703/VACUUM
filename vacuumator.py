import time

import bmp280
from parameters import (
    VP, PRESSURE_RELEASE_TIME_MS, VALVE_OPENED_TOO_FAST_MAX_COUNT,
    VacuumErrors)
from valve import Valve, ReceiverValve
from entity import IntEntity
from bus_sensor import Bus, BusSensor


class Receiver:
    def __init__(
            self, bus_sensor, valve, working, start_pump_press,
            stop_pump_press, pump_work_time
        ):
        self.bus_sensor = bus_sensor
        self.valve = valve
        self.working = working
        self.start_pump_press = start_pump_press
        self.stop_pump_press = stop_pump_press
        self.pump_work_time = pump_work_time
        self.pause_start = 0

    def tact(self):
        self.bus_sensor.update_pressure()
        self.valve.calc_percent()
        if self.pause_start > 0:
            # Если пауза - держим насос выключенным
            # и считаем время (пауза по времени равна максимальному времени работы мотора)
            self.valve.close()
            pause_time = time.ticks_ms() - self.pause_start
            if pause_time > self.pump_work_time.value:
                self.pause_start = 0
            else:
                return
        if self.bus_sensor.error.value != 0 or self.working.value == 0:
            self.valve.close()
            return
        if self.valve.is_open.value == 1:
            if self.bus_sensor.pressure.value < self.stop_pump_press.value:
                self.valve.close()
                return
            working_time = time.ticks_ms() - self.valve.last_time_change
            if working_time > self.pump_work_time.value:
                # если время работы превысило максимальное значение, ставим паузу
                self.pause_start = time.ticks_ms()
                self.valve.close()
                return
        if self.bus_sensor.pressure.value > self.start_pump_press.value:
            self.valve.open()

class Table:
    def __init__(
            self, bus_sensor, table_valve, outer_valve, working,
            start_vac_table, impulse_time, normal_press, start_pump_press,
            min_valve_cycle_period
        ):
        self.bus_sensor = bus_sensor
        self.table_valve = table_valve
        self.outer_valve = outer_valve
        self.working = working
        self.start_vac_table = start_vac_table
        self.impulse_time = impulse_time
        self.min_valve_cycle_period = min_valve_cycle_period
        self.normal_press = normal_press
        self.start_pump_press = start_pump_press
        # Флаг для закрытия выпускного клапана после выравнивания давления:
        self.is_pressure_released = False
        # При включении вакуума на стол первый цикл делаем до более низкого
        # давления (start_pump_press). Это обеспечит лучшее прилегание
        self.is_first_cycle = True
        self.last_time_opened = 0
        self.opened_too_fast_counter = 0

    def _check_opened_too_fast(self):
        time_open_diff = time.ticks_ms() - self.last_time_opened
        if time_open_diff < self.min_valve_cycle_period.value:
            self.opened_too_fast_counter += 1
            if self.opened_too_fast_counter == VALVE_OPENED_TOO_FAST_MAX_COUNT:
                self.opened_too_fast_counter = 0
                self.working.value = 0
                self.bus_sensor.error.set_value(VacuumErrors.FilmError)
        else:
            self.opened_too_fast_counter = 0
        self.last_time_opened = time.ticks_ms()

    def tact(self):
        self.bus_sensor.update_pressure()
        if self.bus_sensor.error.value != 0:
            self.table_valve.close()
            return
        if self.working.value == 1:
            self.is_pressure_released = False
            self.outer_valve.close()
            if self.is_first_cycle:
                threshold_pressure = self.start_pump_press.value
            else:
                threshold_pressure = self.start_vac_table.value
            if self.bus_sensor.pressure.value > threshold_pressure:
                cur_state_time = time.ticks_ms() - self.table_valve.last_time_change
                if cur_state_time >= self.impulse_time.value:
                    self.table_valve.toggle()
                    # if self.table_valve.is_open:
                    #     self._check_opened_too_fast()
            else:
                self.is_first_cycle = False
                self.table_valve.close()
        else:
            self.table_valve.close()
            self.is_first_cycle = True
            if not self.is_pressure_released:
                self.outer_valve.open()
                self.is_pressure_released = True
            # Закрываем выпускной клапан после того, как давление выровнено
            if self.outer_valve.is_open:
                time_opened = time.ticks_ms() - self.outer_valve.last_time_change
                if time_opened > PRESSURE_RELEASE_TIME_MS:
                    self.outer_valve.close()


class Vacuumator3000:
    def __init__(self, i2c, store):
        bus = Bus(i2c)
        sensor = bmp280.BMP280(i2c_bus=i2c, addr=VP.sensor_address,
                               use_case=bmp280.BMP280_CASE_HANDHELD_DYN)

        self.receiver_work = IntEntity(VP.vac_receiver_store_num, 0, store)
        self.table_1_work = IntEntity(VP.vac_table1_store_num, 0, store)
        self.table_2_work = IntEntity(VP.vac_table2_store_num, 0, store)
        self.table_3_work = IntEntity(VP.vac_table3_store_num, 0, store)

        self.start_pump_press = IntEntity(
            VP.start_pump_press_store_num, VP.start_pump_press, store)
        self.stop_pump_press = IntEntity(
            VP.stop_pump_press_store_num, VP.stop_pump_press, store)
        self.start_vac_table = IntEntity(
            VP.start_vac_table_store_num, VP.start_vac_table, store)
        self.normal_press = IntEntity(
            VP.normal_press_store_num, VP.normal_press, store)
        self.pump_work_time = IntEntity(
            VP.pump_work_time_store_num, VP.pump_work_time, store)
        self.impulse_time = IntEntity(
            VP.impulse_time_store_num, VP.impulse_time, store)
        self.min_valve_cycle_period = IntEntity(
            VP.min_valve_cycle_period_store_num, VP.min_valve_cycle_period, store)

        receiver_sensor = BusSensor(
            bus, 0, sensor, store, samples=VP.samples,
            error_store_num=VP.res_sensor_error_store_num,
            pressure_store_num=VP.receiver_pressure_store_num
        )
        receiver_valve = ReceiverValve(
            VP.receiver_valve_pin, store,
            state_store_num=VP.receiver_valve_state_store_num,
            pump_work_percent_store_num=VP.pump_work_percent_store_num
        )
        self.receiver = Receiver(
            receiver_sensor, receiver_valve,
            working=self.receiver_work,
            start_pump_press=self.start_pump_press,
            stop_pump_press=self.stop_pump_press,
            pump_work_time=self.pump_work_time
        )

        t1_sensor = BusSensor(
            bus, 1, sensor, store, samples=VP.samples,
            error_store_num=VP.table1_sensor_error_store_num,
            pressure_store_num=VP.table1_pressure_store_num
        )
        self.table_1 = self.__create_table(
            store, t1_sensor, VP.table1_valve_pin,
            table_state_store_num=VP.table1_valve_state_store_num,
            outer_pin=VP.outer1_valve_pin,
            outer_state_store_num=VP.outer1_valve_state_store_num,
            working=self.table_1_work,
            start_vac_table=self.start_vac_table,
            impulse_time=self.impulse_time,
            normal_press=self.normal_press,
            start_pump_press=self.start_pump_press,
            min_valve_cycle_period=self.min_valve_cycle_period
        )

        t2_sensor = BusSensor(
            bus, 2, sensor, store, samples=VP.samples,
            error_store_num=VP.table2_sensor_error_store_num,
            pressure_store_num=VP.table2_pressure_store_num
        )
        self.table_2 = self.__create_table(
            store, t2_sensor, VP.table2_valve_pin,
            table_state_store_num=VP.table2_valve_state_store_num,
            outer_pin=VP.outer2_valve_pin,
            outer_state_store_num=VP.outer2_valve_state_store_num,
            working=self.table_2_work,
            start_vac_table=self.start_vac_table,
            impulse_time=self.impulse_time,
            normal_press=self.normal_press,
            start_pump_press=self.start_pump_press,
            min_valve_cycle_period=self.min_valve_cycle_period
        )

        t3_sensor = BusSensor(
            bus, 3, sensor, store, samples=VP.samples,
            error_store_num=VP.table3_sensor_error_store_num,
            pressure_store_num=VP.table3_pressure_store_num
        )
        self.table_3 = self.__create_table(
            store, t3_sensor, VP.table3_valve_pin,
            table_state_store_num=VP.table3_valve_state_store_num,
            outer_pin=VP.outer3_valve_pin,
            outer_state_store_num=VP.outer3_valve_state_store_num,
            working=self.table_3_work,
            start_vac_table=self.start_vac_table,
            impulse_time=self.impulse_time,
            normal_press=self.normal_press,
            start_pump_press=self.start_pump_press,
            min_valve_cycle_period=self.min_valve_cycle_period
        )
        self.receiver.working.set_value(1) # Включаем ресивер при старте

    def __create_table(
            self, store, bus_sensor, table_pin, table_state_store_num,
            outer_pin, outer_state_store_num, working, start_vac_table,
            impulse_time, normal_press, start_pump_press, min_valve_cycle_period
        ):
        table_valve = Valve(table_pin, store, state_store_num=table_state_store_num)
        outer_valve = Valve(outer_pin, store, state_store_num=outer_state_store_num)
        return Table(
            bus_sensor, table_valve, outer_valve, working,
            start_vac_table, impulse_time, normal_press, start_pump_press,
            min_valve_cycle_period
        )

    def update_store_values(self):
        self.receiver_work.get_value()
        self.table_1_work.get_value()
        self.table_2_work.get_value()
        self.table_3_work.get_value()
        self.start_pump_press.get_value()
        self.stop_pump_press.get_value()
        self.start_vac_table.get_value()
        self.normal_press.get_value()
        self.pump_work_time.get_value()
        self.impulse_time.get_value()

    def tact(self):
        self.receiver.tact()
        self.table_1.tact()
        self.table_2.tact()
        self.table_3.tact()
