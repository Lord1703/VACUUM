class VP:
    sensor_address = 0x76

    """parameters"""
    start_pump_press = 500
    stop_pump_press = 200
    start_vac_table = 600
    normal_press = 1000
    pump_work_time = 20000
    impulse_time = 50
    samples = 1
    pressure_update_critical_time = 10000
    min_valve_cycle_period = 8000

    """pins"""
    receiver_valve_pin = 8
    table1_valve_pin = 9
    table2_valve_pin = 10
    table3_valve_pin = 11
    outer1_valve_pin = 12
    outer2_valve_pin = 13
    outer3_valve_pin = 14

    """store nums"""
    vac_receiver_store_num = 0
    vac_table1_store_num = 1
    vac_table2_store_num = 2
    vac_table3_store_num = 3

    start_pump_press_store_num = 4
    stop_pump_press_store_num = 5
    start_vac_table_store_num = 6
    normal_press_store_num = 7
    pump_work_time_store_num = 8
    impulse_time_store_num = 9
    pump_work_percent_store_num = 10

    # минимально допустимый период срабатывания клапана стола
    min_valve_cycle_period_store_num = 30

    receiver_valve_state_store_num = 11
    table1_valve_state_store_num = 12
    table2_valve_state_store_num = 13
    table3_valve_state_store_num = 14
    outer1_valve_state_store_num = 15
    outer2_valve_state_store_num = 16
    outer3_valve_state_store_num = 17

    res_sensor_error_store_num = 18
    table1_sensor_error_store_num = 19
    table2_sensor_error_store_num = 20
    table3_sensor_error_store_num = 21

    receiver_pressure_store_num = 22
    table1_pressure_store_num = 24
    table2_pressure_store_num = 26
    table3_pressure_store_num = 28


class VacuumErrors:
    NoError = 0
    SwitchBusError = 1
    InitSensorError = 2
    UpdateTimeError = 3
    FilmError = 4  # Плёнка плохо прилегает или отсутствует


# I2C константы
I2C_NUM = 1
I2C_SDA = 2
I2C_SCL = 3
I2C_FREQ = 400 * 1000

# Константы
PRESSURE_RELEASE_TIME_MS = 200
I2C_RETRIES = 10
VALVE_OPENED_TOO_FAST_MAX_COUNT = 10

# Значение давления при отсутствии готовых данных на BMP280
BMP280_NO_DATA_AVAILABLE = 628.0041
