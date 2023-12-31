from ds18b20 import DS18B20, file_check, read_sensors, write_to_sql_lite, ReadingObj 
from datetime import datetime, timezone
from time import sleep, strftime
from logging import basicConfig as logging_basicConfig, DEBUG as const_DEBUG, info as logging_info, debug as logging_debug, error as logging_error
from subprocess import call as subprocess_call
import firebase_admin_file
from os import chdir as os_chdir, path as os_path
os_chdir(os_path.dirname(os_path.abspath(__file__)))

SENSOR_NAMES = ReadingObj.SENSOR_NAMES
# Sleep interval between readings
#  750ms conversion time + manual 250ms sleep = 1s per sensor read time.
# sensor accuracy = +- 0.0625
INTERVAL = 18.9

# Number of decimal point to round temperature to.
ROUNDING = 2

# Number of physically connected sensors
SENSOR_COUNT = 10

# Maximum errors before system reboot.
MAX_ERRORS = 10

# Storage location 1 - SQLite - local
sqlite_file_1= '/home/luke/Desktop/Script/Output/shared_data.db'

# Storage location 2 - SQLite - USB
sqlite_file_2= '/media/pi/USB4G/Database/shared_data.db'

# Storage location 3 - txt - local
text_output_file = '/home/luke/Desktop/Script/Output/output.txt'

# Storage location 4 - firebase firestore
# firestore_admin_file.py handles this

# keep last reading incase of read failure.
previousReadingObj = None

lastHourDocumentRef = None

error_count_sensors = 0
error_count_other = 0

# Logging settings
# (10 DEBUG, 20 INFO, 30 WARNING, 40 ERROR, 50 CRITICAL)
logging_basicConfig(
    level=const_DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    filename='/home/luke/Desktop/Script/Logs/error_logging.txt',
    filemode='a'
)

def log_reading(message):
    """
    -------------------------------------------------------
    Writes a message to log file.
    Use: log_event("errors.txt", "my error")
    -------------------------------------------------------
    """ 
    with open("/home/luke/Desktop/Script/Logs/write_failures.txt", 'a') as output_file:
        output_file.write(f"{str(datetime.now())}  {message}\n")
    output_file.close()
    return

'''
MAIN LOOP
'''
while True:
    # get temperature sensors
    sensor_obj = DS18B20()
    num_of_sensors = sensor_obj.device_count()

    # datetime for firebase
    date_time_utc = datetime.now(timezone.utc)
    date_time_utc = date_time_utc.replace(minute=0, second=0, microsecond=0)
    #date_time_utc = date_time_utc.astimezone(timezone.utc)

    # create time string
    date_time_now = strftime('%Y-%m-%d %H:%M:%S')

    # Reboot if error count reaches set value. One or more sensors are not detected.
    # Rebooting helps when sensors are not being detected. Log the rest of the sensors.
    if num_of_sensors != SENSOR_COUNT:
        #print(f"____ERROR____   only found {num_of_sensors} / {SENSOR_COUNT} sensors")
        error_count_sensors += 1
        if error_count_sensors >= MAX_ERRORS:
            logging_info(f"_ERROR_ REBOOTING because detected only {num_of_sensors} / {SENSOR_COUNT} sensors.")
            firebase_admin_file.send_notification('notify', 'error', f"REBOOTING because detected only {num_of_sensors} / {SENSOR_COUNT} sensors.")
            sleep(30)
            subprocess_call('sudo reboot', shell=True)
        
        else:
            logging_info(f"_ERROR_ Detected only {num_of_sensors} / {SENSOR_COUNT} sensors.  \
            error Count {error_count_sensors}") 
    '''
    Begin reading sensors
    '''
    try:
        # Read Available Sensors
        #print("reading sensors...")
        readingObj = read_sensors(sensor_obj, previousReadingObj, date_time_now, num_of_sensors, ROUNDING)
        sensor_vals_tuple = readingObj.get_solar_tuple()
        sensor_vals_string = readingObj.get_solar_str()
        
        '''
        -Stage 1 recovery-
        Keep a previous reading in memory incase of sensor read failure.
        Instead of saving None values to db, retrieve last known good value.
        Issue is when ultimate failure occurs.
            i.e system reboots and 1st reading upon boot fails when previous reading is None.
        -Stage 2 recovery-
        Read the sql lite db to find last known good value.
        '''


        # Console Display
        #i = 0
        #for val in sensor_vals_tuple:
            #print("{:<15}  {}".format(SENSOR_NAMES[i], val))
            #i += 1
        
        previousReadingObj = readingObj

        # Storage Location 1 - SQLite
        write_to_sql_lite(sqlite_file_1, sensor_vals_tuple)

        # Storage Location 2 - SQLite USB
        #write_to_sql_lite(sqlite_file_2, sensor_vals_tup)
        
        # Storage Location 3 - text file
        file_check(text_output_file)
        with open(text_output_file, 'a') as output_file:
            # write titles if required
            output_file.write(sensor_vals_string + "\n")
        output_file.close()

        # Storage Location 4 - Firebase firestore
        '''
        Todo: deal with connection exceptions. record timestamps where exception occurs. when connection is restored, write all failed lines to db.
        Merging with previous hours will need to be done.
        '''
        lastHourDocumentRef = firebase_admin_file.write_line(date_time_utc, sensor_vals_string, lastHourDocumentRef, readingObj)

    except ValueError as error:
        '''
         When write to firebase fails.
         "An exception of type ValueError occurred: The transaction has no transaction ID, so it cannot be rolled back."
         TODO
         Write lines to file and upload them when connection is restored.
         Check if file exists. If so, read line by line and firebase.write_line
        '''
        logging_error(f"An exception of type {type(error).__name__} occurred: {str(error)}\n    error_count: {error_count_other}\n\n", exc_info=True)
        log_reading(sensor_vals_string)
        error_count_other += 1

    except Exception as error:
        print(f"---------ERROR----------------\n {error}")
        error_count_other += 1        
        logging_error(f"An exception of type {type(error).__name__} occurred: {str(error)}\n    error_count: {error_count_other}\n\n", exc_info=True)     
        
    finally:        
        #print ('___waiting {} seconds...'.format(INTERVAL))
        if error_count_other >= MAX_ERRORS:
            logging_error(f"REBOOTING due to error count of {error_count_other}.")
            try:
                firebase_admin_file.send_notification('notify', 'error', f"REBOOTING due to error count of {error_count_other}.")
            except:
                logging_error(f"Failed to send notification")
                pass
            sleep(60)
            logging_error(f"REBOOTING now")
            subprocess_call('sudo reboot', shell=True)


        sleep(INTERVAL)
        


