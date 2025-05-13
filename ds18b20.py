from os import system
from glob import glob
from time import sleep, time
from sqlite3 import connect as sqlite_connect
from datetime import datetime
from firebase_admin_file import send_notification
from subprocess import call as subprocess_call
sqlite_file_1= '/home/luke/Desktop/Script/Output/shared_data.db'

HIGH_TEMP_THRESHOLD = 91.5

class ReadingObj:
    """
    -------------------------------------------------------
    Object used to store read sensor values.
    Contains sensor names and calibration values.
    -------------------------------------------------------
    """ 
    def __init__(self):
        self.date_time_now = time()
        self.glycol_in_roof = 0.01 # workaround to stop None from being written
        self.glycol_in = 0.01
        self.glycol_out_st = 0.01
        self.glycol_out_he = 0.01
        self.solar_t_high = 0.01
        self.solar_t_mid = 0.01
        self.solar_t_low = 0.01
        self.boiler_t_mid = 0.01
        self.boiler_t_out = 0.01
        self.solar_t_out = 0.01
        self.ab = None
        self.cd = None
        self.ef = None
        self.gh = None
        self.ij = None
        self.kl = None
        self.mn = None
        self.op = None
        self.qr = None
        self.st = None

    # maps the sensors address to a variable
        self._sensor_mapping = {
            '7b72': 'glycol_in_roof',
            '1e37': 'glycol_in',
            '9e0f': 'glycol_out_st',
            '4ee6': 'glycol_out_he',
            'f5d6': 'solar_t_high',
            '071a': 'solar_t_mid',
            '839e': 'solar_t_low',
            '1a77': 'boiler_t_mid',
            'd995': 'boiler_t_out',
            'f969': 'solar_t_out',
            # new sensors. Not in use.
            '78a2': "ab",
            '91ed': "cd",
            'a85c': "ef",
            'a0b0': "gh",
            '7bc2': "ij",
            '317c': "kl",
            '7176': "mn",
            '6ebd': "op",
            'dad9': "qr",
            'b9fd': "st"
            }

    # sensor calibration.
        self._adjustment_values = {
            # original solar system sensors (2020)
            '9e0f': 0.567,
            '1e37': 0,
            '839e': -0.29,
            '4ee6': 0.35,
            '071a': 0.552,
            '7b72': -0.045,
            'd995': -0.165,
            'f5d6': 0.045,
            'f969': -0.636,
            '1a77': 0.142,
            # new sensors (12/2023)
            '78a2': -0.2788,
            '91ed': 0.2878,
            'a85c': -0.208,
            'a0b0': -0.0416,
            '7bc2': 0.2128,
            '317c': 0.0413,
            '7176': 0.4028,
            '6ebd': -0.5231,
            'dad9': 0.2513,
            'b9fd': -0.1445}

    def __iter__(self):
        return iter([
            self.glycol_in_roof,
            self.glycol_in,
            self.glycol_out_st,
            self.glycol_out_he,
            self.solar_t_high,
            self.solar_t_mid,
            self.solar_t_low,
            self.boiler_t_mid,
            self.boiler_t_out,
            self.solar_t_out,
            self.ab,
            self.cd,
            self.ef,
            self.gh,
            self.ij,
            self.kl,
            self.mn,
            self.op,
            self.qr,
            self.st])

    def print_not_none(self):
        '''
        Returns a string of sensors that are not none.\n
        Useful when testing new sensors.
        '''
        not_none_attr = {attr: getattr(self, attr) 
            for attr in dir(self) 
            if not callable(getattr(self, attr)) 
            and not attr.startswith("__") 
            and not attr.startswith("_") 
            and getattr(self, attr) is not None}
        
        return ', '.join(f"{key},{value}" for key, value in not_none_attr.items())
    

    def get_solar_tuple(self):
        """
        Returns a tuple with ordered data for the solar system logger.
        """
        sensor_vals_tup = (self.date_time_now,
        self.glycol_in_roof,
        self.glycol_in,
        self.glycol_out_st,
        self.glycol_out_he,
        self.solar_t_high,
        self.solar_t_mid,
        self.solar_t_low,
        self.boiler_t_mid,
        self.boiler_t_out,
        self.solar_t_out)

        return sensor_vals_tup
    
    def get_solar_str(self):
        # returns a string from a tuple.
        return ','.join(map(str, self.get_solar_tuple()))


    def __str__(self):
        '''
        To String
        '''
        return (
            f"glycol_in_roof: {self.glycol_in_roof}, "
            f"glycol_in: {self.glycol_in}, "
            f"glycol_out_st: {self.glycol_out_st}, "
            f"glycol_out_he: {self.glycol_out_he}, "
            f"solar_t_high: {self.solar_t_high}, "
            f"solar_t_mid: {self.solar_t_mid}, "
            f"solar_t_low: {self.solar_t_low}, "
            f"boiler_t_mid: {self.boiler_t_mid}, "
            f"boiler_t_out: {self.boiler_t_out}, "
            f"solar_t_out: {self.solar_t_out}, "
            f"ab: {self.ab}, "
            f"cd: {self.cd}, "
            f"ef: {self.ef}, "
            f"gh: {self.gh}, "
            f"ij: {self.ij}, "
            f"kl: {self.kl}, "
            f"mn: {self.mn}, "
            f"op: {self.op}, "
            f"qr: {self.qr}, "
            f"st: {self.st}")
    
    # ordered list of sensor names for solar system logger 
    SENSOR_NAMES = [
        'Date',
        'glycol_in_roof',
        'glycol_in',
        'glycol_out_st',
        'glycol_out_he',
        'solar_t_high',
        'solar_t_mid',
        'solar_t_low',
        'boiler_t_mid',
        'boiler_t_out',
        'solar_t_out']


class DS18B20:
    '''
    -------------------------------------------------------
     Much of this code is lifted from Adafruit web site
     This class can be used to access one or more DS18B20 temperature sensors
     It uses OS supplied drivers and one wire support must be enabled
     To do this add thi line for defaulting to gpiopin4 or select another pin
     dtoverlay=w1-gpio,gpiopin=26   (master1)
     dtoverlay=w1-gpio,gpiopin=6    (master2)
     to the end of /boot/config.txt
    -------------------------------------------------------
     The DS18B20 has three pins, looking at the flat side with the pins pointing
        down pin 1 is on the left
     Connect pin 1 to GPIO ground
     Connect pin 2 to GPIO input pin and GPIO 3.3V via a 4k7 (4.7k ohm) pullup resistor
     Connect pin 3 to GPIO 3.3V (or 5V)
     You can connect more than one sensor to the same set of pins.
     Only one pullup resistor is required.
    '''
    def __init__(self):
        # load required kernel modules
        system('/usr/sbin/modprobe w1-gpio')
        system('/usr/sbin/modprobe w1-therm')     
        # Find file names for the sensor(s)
        base_dir = '/sys/bus/w1/devices/'
        device_folder = glob(base_dir + '28*')
                
        self.device_folder = device_folder
        self._num_devices = len(device_folder)
        self._device_file = list()
        i = 0
        while i < self._num_devices:
            self._device_file.append(device_folder[i] + '/w1_slave')
            i += 1
        
    def _read_temp(self,index):
        # Issue one read to one sensor
        # you should not call this directly
        sleep(0.25)
        try:
            f = open(self._device_file[index],'r')
        except:
            # getting around FileNotFoundError preventing the retries in get_tempC
            log_event(f"FileNotFoundError for index {index}")
            return []
        lines = f.readlines()
        f.close()
        return lines
        
    def get_tempC(self,index = 0):
        """
        -------------------------------------------------------
        Returns the value for a sensor.
        Returns 998 or 999 if the read failed. 
        Use: s_value = sensor_obj.get_tempC(i)
        -------------------------------------------------------
        Parameters:
            i - index of the element to access (int)
        Returns:
            value - a float value for temperature (float)
        -------------------------------------------------------
        """
        # read sensor temperature in degrees C
        lines = self._read_temp(index)
        retries = 12
        interval = 2
        # read failed. sensor file is empty. Try again.
        if len(lines) == 0:                        
            # retry a few times before giving up
            while (len(lines) == 0) and (retries > 0):                
                sleep(interval)
                interval += 2
                retries -= 1
                lines = self._read_temp(index)
                log_event("list len {} | failed index {}    read retried.  retries remaining {}".format(str(len(lines)),str(index),str(retries)))
                if (retries <= 0):
                    send_notification('debug','read failed',f'{datetime.now().strftime("%a %I:%M %p")} Index {index}. retries remaining {str(retries)}')
            # read failed
            if len(lines) == 0:
                    log_event("get_tempC read FAILED")  
                    #----------------  
                    # attempt to prevent None from being written
                    try:
                        send_notification('debug', 'error', f'Rebooting @ {datetime.now().strftime("%a %I:%M %p")}. Sensor Failed to read.')
                    except:
                        log_event(f"Failed to send notification")
                        pass
                    sleep(60)
                    log_event(f"Rebooting. Sensor Failed to read. Ultimate failure")
                    subprocess_call('sudo reboot', shell=True)
                    #-----------------
                    #return None
        
        retries = 10
        while (lines[0].strip()[-3:] != 'YES') and (retries > 0):
            # read failed so try again
            log_event(" file is not empty but 'YES' not found. trying again.  retries: {}".format(str(retries)))
            lines = self._read_temp(index)
            retries -= 1
            
        if retries == 0:
            # error
            return None
            
        equals_pos = lines[1].find('t=')
        if equals_pos != -1:
            temp = lines[1][equals_pos + 2:]
            temp = float(temp)/1000
            device_name = self.device_folder[index][-4:]
            temp = calibration(device_name,temp)
            #print(temp)
            
            # avoid recording nonsensical values.
            # TODO keep a running average and use that instead of this. 
            # problem is with fast temp swings such as when system turns on or water turns on. 
            # sensor can read -55 to 125.
            
            # FIXME this is not a good place to check for this.
            # could lead to infinite loop. hasnt happened yet
            if (temp < -60) or (temp > 150):
                sleep(2)
                log_event(f"nonsense temp value encountered at {device_name} and {temp}")
                # retry
                temp = self.get_tempC(index)
            return temp
        else:
            # error
            return None
            
    def device_count(self):
        # call this to see how many sensors have been detected
        return self._num_devices
    
    def get_device_name(self, i):
        # Return the devices ids last 4 characters 
        device_name = self.device_folder[i][-4:]
        return device_name
    

'''
FUNCTIONS
'''

def file_check(file_name):
    """
    -------------------------------------------------------
    Checks if file exists, if not then writes the first line with the sensor names.
    Use: file_check()
    -------------------------------------------------------
    Parameters:
        file_name = the name of the file to check (str)
    Returns:
        none
    -------------------------------------------------------
    """
    try:
        output_file = open(file_name, 'r')
    except:    
        with open(file_name, 'w') as output_file:
            output_file.write(','.join(map(str, ReadingObj.SENSOR_NAMES)) + '\n')
    finally:
        output_file.close()
    return


def write_to_sql_lite(db_location, sensor_values):
    '''
    db_location - (string) location of sql_lite db \n
    sensor_values - (tuple) Sensor values
    '''
    conn = sqlite_connect(db_location)
    c = conn.cursor()
    c.execute(f"""CREATE TABLE IF NOT EXISTS "temperature" (
        "{ReadingObj.SENSOR_NAMES[0]}" DATETIME NULL,
        "{ReadingObj.SENSOR_NAMES[1]}" INTEGER NULL,
        "{ReadingObj.SENSOR_NAMES[2]}" INTEGER NULL,
        "{ReadingObj.SENSOR_NAMES[3]}" INTEGER NULL,
        "{ReadingObj.SENSOR_NAMES[4]}" INTEGER NULL,
        "{ReadingObj.SENSOR_NAMES[5]}" INTEGER NULL,
        "{ReadingObj.SENSOR_NAMES[6]}" INTEGER NULL,
        "{ReadingObj.SENSOR_NAMES[7]}" INTEGER NULL,
        "{ReadingObj.SENSOR_NAMES[8]}" INTEGER NULL,
        "{ReadingObj.SENSOR_NAMES[9]}" INTEGER NULL,
        "{ReadingObj.SENSOR_NAMES[10]}" INTEGER NULL)""")
    c.execute("INSERT INTO temperature VALUES(?,?,?,?,?,?,?,?,?,?,?)", sensor_values)
    conn.commit()
    conn.close()
    return

def get_last_known_value_sql(db_location, index):
    '''
    When sensor fails to read, retrieve last value from db to prevent None from being written to db.
    '''
    conn = sqlite_connect(db_location)
    c = conn.cursor()
    column_name = ReadingObj.SENSOR_NAMES[index]
    c.execute(f'SELECT {column_name} from temperature ORDER BY "Date" DESC LIMIT 1;')
    result = c.fetchone()    
    conn.commit()
    conn.close()
    if result:
        return result[0]
    else:
        log_event("Failed to retrieve from DB")
        return None

def read_sensors(sensor_obj, previousReadingObj, date_time_now, num_of_sensors, ROUNDING):
    '''
    -------------------------------------------------------
    sensor_obj - (DS18B20 object)
    date_time_now - (string) date '%Y-%m-%d %H:%M:%S'
    previousReadingObj - last reading incase of failure.
    num_of_sensors - preset number of connceted sensors
    ROUNDING - value to round to
    -------------------------------------------------------
    Returns - ReadingObj
    '''
    reading_obj = ReadingObj()
    reading_obj.date_time_now = date_time_now
    RETRIES = 5
    # read each sensor
    #print(f"{num_of_sensors}")
    i = 0
    while i < num_of_sensors:
        # get sensor name and value
        s_name = sensor_obj.get_device_name(i)
        s_value = sensor_obj.get_tempC(i)
        
                    # Overheating notification
        # get a second reading beore sending a notification
        if (s_value > HIGH_TEMP_THRESHOLD):
            s_value = sensor_obj.get_tempC(i)
            if (s_value > HIGH_TEMP_THRESHOLD):
                send_notification('hot','Temperature limit exceeded', f"{reading_obj._sensor_mapping[s_name]} reported {round(s_value, ROUNDING)} C")
        #print (f"{i+1} {reading_obj._sensor_mapping[s_name]} {s_value}")
        if s_value is not None:
            # temp read succesfully
            s_value = round(s_value, ROUNDING) 
        else:
            # read failed
            log_event("Sensor read FAILED.  previousReadingObj is None. Fetching from DB ")
            s_value = get_last_known_value_sql(sqlite_file_1, i)
            log_event(f"retrieved from DB  {s_name} = {s_value}")  
            # if previousReadingObj is not None:
            #     # get value from previous value held in memory          
            #     s_value = getattr(previousReadingObj, previousReadingObj._sensor_mapping[s_name])
            #     log_event("Sensor read FAILED.  Retrieving last known temperature of {}  {}".format(previousReadingObj._sensor_mapping[s_name], s_value))
            # else:
            #     log_event("Sensor read FAILED.  previousReadingObj is None. Fetching from DB ")
            #     s_value = get_last_known_value_sql(sqlite_file_1, i)
            #     log_event(f"retrieved from DB  {s_name} = {s_value}")                

        
        # if its still None for some reason
        if s_value is None:
            # still failed, try again .
            j = 0
            while s_value is None and j < RETRIES:
                log_event("Sensor read FAILED.  Retrying read again ")
                sleep(10)
                s_value = sensor_obj.get_tempC(i)
                j += 1
                
            if s_value is None:
                # Ultimate failure. Reboot.
                # FIXME  Handle all read errors in one place.  logging is now broken.
                try:
                    send_notification('debug', 'error', f'Reboot @ {datetime.now().strftime("%a %I:%M %p")}. Ultimate sensor read failure.')
                except:
                    log_event(f"Failed to send notification")
                    pass
                sleep(60)
                log_event(f"Rebooting. Sensor Failed to read. Ultimate failure")
                subprocess_call('sudo reboot', shell=True)

        # set the correct variable in reading object
        #print (f'{i} {reading_obj._sensor_mapping[s_name]} = {s_value}')
        if s_value is None:
            send_notification('debug', 'error', f'NULL got through {datetime.now().strftime("%a %I:%M %p")}')
        setattr(reading_obj, reading_obj._sensor_mapping[s_name], s_value)
        i += 1      
        #print(reading_obj._sensor_mapping[s_name], " ", s_value)
    return reading_obj
    
def calibration(name, temp_c):
    """
    -------------------------------------------------------
    Returns the calibrated value for a sensor.
    Calibration values are hardcoded from previous testing. 
    Use: value = calibration(device_name,value)
    -------------------------------------------------------
    Parameters:
        device_name - the device name/address (str)
        temp_c - a float value for temperature (float)
    Returns:
        temp_c - a float value for temperature (float)
    -------------------------------------------------------
    """ 
    readingObj = ReadingObj()
    temp_c += readingObj._adjustment_values[name]
    
    return temp_c

def log_event(message):
    """
    -------------------------------------------------------
    Writes a message to log file.
    Use: log_event("errors.txt", "my error")
    -------------------------------------------------------
    """ 
    with open("/home/luke/Desktop/Script/Logs/errors_ds18b20.txt", 'a') as output_file:
        output_file.write(f"{str(datetime.now())}  {message}\n")
    output_file.close()
    return
