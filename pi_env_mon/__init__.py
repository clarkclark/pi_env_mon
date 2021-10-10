# merge progs for LCD plate and scd41; 2021-10-02 cewood pycharm 2021-10-03
# note LCD cursor_position is COLUMN,ROW (0-15, 0-1)

# /home/pi/venv/pi_env_mon/bin/python /home/pi/pi_env_mon/pi_env_mon/__init__.py

import os  # os is brought in to allow SHUTDOWN of RasPi from the 'down' button (just before DATE displays)
import time
import board  # pip install Adafruit-Blinka
import busio  # pip install Adafruit-Blinka
import adafruit_scd4x  # pip install adafruit-circuitpython-scd4x
import adafruit_character_lcd.character_lcd_rgb_i2c as character_lcd  # pip install adafruit-circuitpython-charlcd

from monitor_air_quality import monitor_air_quality

lcdi2c = board.I2C()
lcd_columns = 16
lcd_rows = 2
co2i2c = busio.I2C(board.SCL, board.SDA)

# Initialise the LCD class
lcd = character_lcd.Character_LCD_RGB_I2C(lcdi2c, lcd_columns, lcd_rows)

lcd.color = [100, 0, 0]  # NOT a RGB text display, but all three values needed

scd4x = adafruit_scd4x.SCD4X(co2i2c)
scd4x.start_periodic_measurement()
while True:
    if scd4x.data_ready:
        # display date & time
        local_time = time.localtime()
        print()
        print(time.strftime('%Y-%m-%d %H:%M', local_time))
        lcd.cursor_position(0, 0)
        lcd.message = (time.strftime('%Y-%m-%d %H:%M', local_time))
        lcd.cursor_position(0, 1)
        lcd.message = ("(buttons active)")
        time.sleep(5)   #DATE & TIME DISPLAYED, RESPOND TO BUTTONS NOW!
        if lcd.select_button:
            lcd.message = "Select!"
        if lcd.left_button:
           lcd.message = "Left!"
        if lcd.right_button:
            lcd.message = "Right!"
        if lcd.up_button:
            lcd.message = "Up!"
        if lcd.down_button:
            print("Shutting Down")
            lcd.cursor_position(0, 0)
            lcd.message = "Shutting Down!!!"
            lcd.cursor_position(0, 1)
            lcd.message = "Shutting Down!!!"
            time.sleep(5)
            lcd.color = [0, 0, 0]
            os.system("sudo shutdown -h now")

    # display temperature
        lcd.clear()
        tempF = ((scd4x.temperature * 1.8) + 32)
        print("%0.1f*F" % tempF)
        lcd.cursor_position(0, 0)
        lcd.message = ("%0.1f*F" % tempF)
    #display relative_humidity
        print("%0.1f%% RH" % scd4x.relative_humidity)
        lcd.cursor_position(8, 0)
        lcd.message = ("%0.1f%% RH" % scd4x.relative_humidity)
    # display CO2 level
        print("%d ppm CO2" % scd4x.CO2)
        lcd.cursor_position(0, 1)
        lcd.message = ("%d ppm CO2" % scd4x.CO2)

    # get and display PM & AQI
        air_quality_data = monitor_air_quality.get_air_quality()
        print()
        lcd.clear()

        print ("pm25", end =" ")
        print (air_quality_data['pm25'])
        lcd.cursor_position(0, 0)
        lcd.message = ("PM25")
        lcd.cursor_position(5, 0)
        lcd.message = (air_quality_data['pm25'])

        print("aqi25", end =" ")
        print(air_quality_data['aqipm25'])
        lcd.cursor_position(9, 0)
        lcd.message = ("AQI")
        lcd.cursor_position(13, 0)
        lcd.message = (air_quality_data['aqipm25'])

        print("pm10", end =" ")
        print(air_quality_data['pm10'])
        lcd.cursor_position(0, 1)
        lcd.message = ("PM10")
        lcd.cursor_position(5, 1)
        lcd.message = (air_quality_data['pm10'])

        print("aqi10", end =" ")
        print(air_quality_data['aqipm10'])
        lcd.cursor_position(9, 1)
        lcd.message = ("AQI")
        lcd.cursor_position(13, 1)
        lcd.message = (air_quality_data['aqipm10'])
    time.sleep(20)
