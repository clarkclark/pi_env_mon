# merge progs for LCD plate and scd41; 2021-10-02 cewood pycharm 2021-10-03
# massive changes from Gene; massive confusion from Git 2021-10-11
# note LCD cursor_position is COLUMN,ROW (0-15, 0-1)

# /home/pi/venv/pi_env_mon/bin/python /home/pi/pi_env_mon/pi_env_mon/__init__.py

import os  # os is brought in to allow SHUTDOWN of RasPi from the 'down' button (just before DATE displays)
import time
import pathlib
import logging
import board  # pip install Adafruit-Blinka
import busio  # pip install Adafruit-Blinka
import adafruit_scd4x  # pip install adafruit-circuitpython-scd4x
import adafruit_character_lcd.character_lcd_rgb_i2c as character_lcd  # pip install adafruit-circuitpython-charlcd
from sds011 import SDS011  # py-sds011
import aqi  # python-aqi


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        filename='/home/pi/pi_env_mon.log',
        filemode='a')
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s %(message)s')
    console.setFormatter(formatter)
    logging.getLogger().addHandler(console)


def watch_buttons(lcd, seconds):
    end_time = time.time() + seconds
    while time.time() < end_time:
        if lcd.select_button:
            lcd.message = "Select!"
        if lcd.left_button:
            lcd.message = "Left!"
        if lcd.right_button:
            lcd.message = "Right!"
        if lcd.up_button:
            lcd.message = "Up!"
        if lcd.down_button:
            logging.info("Shutting Down")
            lcd.cursor_position(0, 0)
            lcd.message = "Shutting Down!!!"
            lcd.cursor_position(0, 1)
            lcd.message = "Shutting Down!!!"
            time.sleep(5)
            lcd.color = [0, 0, 0]
            os.system("sudo shutdown -h now")


def start_capturing_aqi(sensor):
    # sudo usermod -a -G dialout yourusername
    # https://cdn.sparkfun.com/assets/parts/1/2/2/7/5/Laser_Dust_Sensor_Control_Protocol_V1.3.pdf

    # Start in reporting mode : query/home/pi/.local/bin
    sensor.set_work_period(work_time=0)  # work_time is continuous
    logging.debug('waking sensor')
    sensor.sleep(sleep=False)  # wake sensor


def stop_capturing_aqi(sensor):
    logging.debug('running sensor query')
    result = sensor.query()
    logging.debug('sleeping sensor')
    sensor.sleep()  # sleep sensor
    if result is None:
        logging.error("Sensor returned None")
        return None
    pm25, pm10 = result
    data = {
        'pm25': str(pm25),
        'pm10': str(pm10),
        'aqipm25': str(aqi.to_iaqi(aqi.POLLUTANT_PM25, str(pm25))),
        'aqipm10': str(aqi.to_iaqi(aqi.POLLUTANT_PM10, str(pm10)))
    }
    return data


def fetch_and_display_data(scd4x, lcd):
    # display date & time
    local_time = time.localtime()
    lcd.cursor_position(0, 0)
    lcd.message = (time.strftime('%Y-%m-%d %H:%M', local_time))
    lcd.cursor_position(0, 1)
    lcd.message = "(buttons active)"
    watch_buttons(lcd, 5)  # DATE & TIME DISPLAYED, RESPOND TO BUTTONS NOW!
    # display temperature
    lcd.clear()
    temp_f = ((scd4x.temperature * 1.8) + 32)
    logging.info("%0.1f*F" % temp_f)
    lcd.cursor_position(0, 0)
    lcd.message = ("%0.1f*F" % temp_f)
    # display relative_humidity
    logging.info("%0.1f%% RH" % scd4x.relative_humidity)
    lcd.cursor_position(8, 0)
    lcd.message = ("%0.1f%% RH" % scd4x.relative_humidity)
    # display CO2 level
    logging.info("%d ppm CO2" % scd4x.CO2)
    lcd.cursor_position(0, 1)
    lcd.message = ("%d ppm CO2" % scd4x.CO2)


def fetch_and_display_aqi(lcd):
    # get and display PM & AQI
    sensor = SDS011("/dev/ttyUSB0", use_query_mode=True)
    start_capturing_aqi(sensor)
    try:
        watch_buttons(lcd, 30)
    except KeyboardInterrupt:
        stop_capturing_aqi(sensor)
        raise
    air_quality_data = stop_capturing_aqi(sensor)
    print()
    lcd.clear()

    logging.info(f"pm25 ${air_quality_data['pm25']}")
    lcd.cursor_position(0, 0)
    lcd.message = "PM25"
    lcd.cursor_position(5, 0)
    lcd.message = (air_quality_data['pm25'])

    logging.info(f"aqi25 ${air_quality_data['aqipm25']}")
    lcd.cursor_position(9, 0)
    lcd.message = "AQI"
    lcd.cursor_position(13, 0)
    lcd.message = (air_quality_data['aqipm25'])

    logging.info(f"pm10 ${air_quality_data['pm10']}")
    lcd.cursor_position(0, 1)
    lcd.message = "PM10"
    lcd.cursor_position(5, 1)
    lcd.message = air_quality_data['pm10']

    logging.info(f"aqi10 ${air_quality_data['aqipm10']}")
    lcd.cursor_position(9, 1)
    lcd.message = "AQI"
    lcd.cursor_position(13, 1)
    lcd.message = (air_quality_data['aqipm10'])


def main():
    setup_logging()
    lcdi2c = board.I2C()
    lcd_columns = 16
    lcd_rows = 2
    co2i2c = busio.I2C(board.SCL, board.SDA)

    # Initialise the LCD class
    lcd = character_lcd.Character_LCD_RGB_I2C(lcdi2c, lcd_columns, lcd_rows)

    lcd.color = [100, 0, 0]  # NOT a RGB text display, but all three values needed

    scd4x = adafruit_scd4x.SCD4X(co2i2c)
    scd4x.start_periodic_measurement()

    try:
        while True:
            if scd4x.data_ready:
                fetch_and_display_data(scd4x, lcd)
            if pathlib.Path('/dev/ttyUSB0').exists():
                fetch_and_display_aqi(lcd)
            watch_buttons(lcd, 20)
    except KeyboardInterrupt:
        logging.info("Exiting")
        exit(0)


if __name__ == "__main__":
    main()
