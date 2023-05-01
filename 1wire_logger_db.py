"""
Author: Luke Tatarsky
Created: 1_9_2021
Modified: 5_1_2023
"""
from ds18b20 import DS18B20, file_check
from datetime import datetime
import time, sqlite3
from sys import exc_info
import subprocess


# Number of seconds between readings, + (0.75s * # of sensors)(7.5s)
INTERVAL = 22 

# Number of decimal point to round temperature to.
ROUNDING = 2

# Number of physically connected sensors
SENSOR_COUNT = 9
#output_file_name = '/home/pi/temp_logger/temp_log.txt'

error_count_sensors = 0
error_count_other = 0

def write_to_db(stup):
    # connect to the database. keep this connection short, connect after all sensors have been read.
    # Storage location 1

    conn = sqlite3.connect('/home/pi/temp_logger/solar_temperature_data.db')
    c = conn.cursor()
    # insert into database command.
    c.execute("""CREATE TABLE IF NOT EXISTS "temperature" (
        "Date_Time" DATETIME NULL,
        "glycol_in" INTEGER NULL,
        "glycol_out" INTEGER NULL,
        "solar_high" INTEGER NULL,
        "solar_mid" INTEGER NULL,
        "solar_low" INTEGER NULL,
        "solar_lowest" INTEGER NULL,
        "boiler_mid" INTEGER NULL,
        "boiler_out" INTEGER NULL,
        "solar_out" INTEGER NULL);""")
    c.execute("INSERT INTO temperature VALUES(?,?,?,?,?,?,?,?,?,?)", stup)
    # commit all changes to database
    conn.commit()
    # close the database
    conn.close()
    
    # Storage location 2
    conn2 = sqlite3.connect('/home/pi/pishare/shared_data.db')
    c2 = conn2.cursor()
    c2.execute("""CREATE TABLE IF NOT EXISTS "temperature" (
        "Date_Time" DATETIME NULL,
        "glycol_in" INTEGER NULL,
        "glycol_out" INTEGER NULL,
        "solar_high" INTEGER NULL,
        "solar_mid" INTEGER NULL,
        "solar_low" INTEGER NULL,
        "solar_lowest" INTEGER NULL,
        "boiler_mid" INTEGER NULL,
        "boiler_out" INTEGER NULL,
        "solar_out" INTEGER NULL)""")
    c2.execute("INSERT INTO temperature VALUES(?,?,?,?,?,?,?,?,?,?)", stup)
    conn2.commit()
    conn2.close()

    # Storage location 3
    conn3 = sqlite3.connect('/media/pi/USB4G/Database/shared_data.db')
    c3 = conn3.cursor()
    c3.execute("""CREATE TABLE IF NOT EXISTS "temperature" (
        "Date_Time" DATETIME NULL,
        "glycol_in" INTEGER NULL,
        "glycol_out" INTEGER NULL,
        "solar_high" INTEGER NULL,
        "solar_mid" INTEGER NULL,
        "solar_low" INTEGER NULL,
        "solar_lowest" INTEGER NULL,
        "boiler_mid" INTEGER NULL,
        "boiler_out" INTEGER NULL,
        "solar_out" INTEGER NULL);""")
    c3.execute("INSERT INTO temperature VALUES(?,?,?,?,?,?,?,?,?,?)", stup)
    conn3.commit()
    conn3.close()  

def get_temps():
    # reset values to none, incase the sensor doesnt get read.
    glycol_in = None
    glycol_out = None
    solar_high = None
    solar_mid = None
    solar_low = None
    solar_lowest = None
    boiler_mid = None
    boiler_out = None
    solar_out = None
    
    # create time string
    date_time_now = time.strftime('%Y-%m-%d %H:%M:%S')
    #print(date_time_now)

        
    # read each sensor
    i = 0
    while i < num_of_sensors:
        # call the sensor read function
        s_value = round(sensor_obj.get_tempC(i), ROUNDING)
        s_name = sensor_obj.get_device_name(i)

        # debug line
        #print(" - now reading {} - {}".format(s_name, s_value))
        
        # Calibration for each sensor is done at ds18b20.py
        if s_name == '839e':
            glycol_in = round(float(s_value),ROUNDING)
        elif s_name == '4ee6':
            glycol_out = round(float(s_value),ROUNDING)
        elif s_name == '9e0f':
            solar_high = round(float(s_value),ROUNDING)
        elif s_name == 'd995':
            solar_mid = round(float(s_value),ROUNDING)
        elif s_name == 'f969':
            solar_low = round(float(s_value),ROUNDING)
        elif s_name == '1e37':
            solar_lowest = round(float(s_value),ROUNDING)
        elif s_name == '1a77':
            boiler_mid = round(float(s_value),ROUNDING)
        elif s_name == 'f5d6':
            boiler_out = round(float(s_value),ROUNDING)
        elif s_name == '071a':
            solar_out = round(float(s_value),ROUNDING)
        
        
        
        i += 1

    stup = (date_time_now, glycol_in, glycol_out, solar_high, solar_mid,\
                solar_low, solar_lowest, boiler_mid, boiler_out, solar_out,)
    return stup


while True:

    
    
    # read all sensors
    try:
        # test temperature sensors
        sensor_obj = DS18B20()
        num_of_sensors = sensor_obj.device_count()

        # log this as an error, since it should be equal.
        # still want to record the rest of the sensors.
        # it helps to reboot when sensors arent detected 
        if num_of_sensors != SENSOR_COUNT:
            error_log = open('/home/pi/temp_logger/error_log.txt', 'a+')  
            time_now = time.strftime('%Y-%m-%d %H:%M:%S')            
            error_count_sensors += 1

            # after 10 failed attempts to get all sensors, reboot
            if error_count_sensors == 10:
                error_log.write('{} REBOOTING because num_of_sensors is not 9. num_of_sensors:,{}\n'.format\
                            (time_now, num_of_sensors))
                error_log.close()
                # wait a little and reboot
                time.sleep(30)
                subprocess.run(['sudo', 'reboot'])
                
            error_log.write('{} num_of_sensors is not 9. num_of_sensors:,{} Error Count {}\n'.format\
                            (time_now, num_of_sensors, error_count_sensors))
            error_log.close()

        # debug line
        print("# of sensors: {}".format(num_of_sensors))

        # create a tuple    
        stup = get_temps()   

        write_to_db(stup)
       
        
    except Exception as error:
        #print("---------ERROR----------------")
        
        date_time_now = time.strftime('%Y-%m-%d %H:%M:%S')
        # error logging
        error_log = open('/home/pi/temp_logger/error_log.txt', 'a+')
        exc_type, exc_value, exc_traceback = exc_info()
        
        # this happens very rarely.
        error_count_other += 1
        if error_count_other == 10:
                  
            error_log.write('{} REBOOTING because you got an error on line: {}, count:{} - {}\n'.format\
                        (date_time_now, exc_traceback.tb_lineno, error_count_other, error))
            error_log.close()
            time.sleep(60)
            subprocess.call('sudo reboot', shell=True)
            
        
        error_log.write('{} you got an error on line: {}, count:{} - {}\n'.format\
                        (date_time_now, exc_traceback.tb_lineno, error_count_other, error))
        error_log.close()
        

        
    finally:
        
        print ('___waiting {} seconds...'.format(INTERVAL))
        time.sleep(INTERVAL)


