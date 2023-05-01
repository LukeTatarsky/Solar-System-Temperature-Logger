'''
------------------------------------------------------------------------
	 much of this code is lifted from Adafruit web site. made some additions such as calibration.
	 This class can be used to access one or more DS18B20 temperature sensors
	 It uses OS supplied drivers and one wire support must be enabled
	 To do this add the line
	 	dtoverlay=w1-gpio
	 to the end of /boot/config.txt
	
	 The DS18B20 has three pins, looking at the flat side with the pins pointing
	 down pin 1 is on the left
	 connect pin 1 to GPIO ground
	 connect pin 2 to GPIO 4 *and* GPIO 3.3V via a 4k8 (4800 ohm) pullup resistor
	 connect pin 3 to GPIO 3.3V
	 You can connect more than one sensor to the same set of pins
	 Only one pullup resistor is required
------------------------------------------------------------------------
Author: Adafruit
------------------------------------------------------------------------
'''
import os
import glob
import time

class DS18B20:
	
	def __init__(self):
		# load required kernel modules
		os.system('modprobe w1-gpio')
		os.system('modprobe w1-therm')
		
		# Find file names for the sensor(s)
		base_dir = '/sys/bus/w1/devices/'
		device_folder = glob.glob(base_dir + '28*')
		
		self.device_folder = device_folder
		self._num_devices = len(device_folder)
		self._device_file = list()
		i = 0
		while i < self._num_devices:
			self._device_file.append(device_folder[i] + '/w1_slave')
			i += 1
		
	def _read_temp(self,index):
		'''
		reads the sensor file. returns a list
		'''
		# Issue one read to one sensor
		# you should not call this directly
		f = open(self._device_file[index],'r')
		#print(self._device_file[index])
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
		# call this to get the temperature in degrees C
		# detected by a sensor
		lines = self._read_temp(index)
		retries = 5
		while (lines[0].strip()[-3:] != 'YES') and (retries > 0):
			# read failed so try again
			time.sleep(0.1)
			lines = self._read_temp(index)
			retries -= 1
			
		if retries == 0:
			return 998
			
		equals_pos = lines[1].find('t=')
		if equals_pos != -1:
			temp = lines[1][equals_pos + 2:]
			temp = float(temp)/1000
			device_name = self.device_folder[index][-4:]
			temp = calibration(device_name,temp)
			return temp
		else:
			# error
			return 999
			
	def device_count(self):
		# call this to see how many sensors have been detected
		return self._num_devices
	
	def get_device_name(self, i):
		device_name = self.device_folder[i][-4:]
		return device_name
	
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
		exists = True

	except:    
		exists = False

	if exists == False:
		output_file = open(file_name, 'w')
		output_file.write(',,,{},,{},,{},,{},,{},,{},,{},,{},,{},,{}'\
              	.format('Glycol In',\
                      'Glycol Out',\
                       'Panel High Temp',\
                       'Solar Tank Mid',\
                       'Solar Tank High',\
                       'Boiler Hot Out',\
                       'Solar Tank Low',\
                        'Solar Tank Lowest',\
                       'Boiler Mid',\
                        'Solar Tank Hot Out\n'))           
	output_file.close()
	return
def calibration(name,temp_c):
	"""
    -------------------------------------------------------
    Returns the calibrated value for a sensor.
    Calibration values are hardcoded from previous testing. 
    Use: value = calibration(device_name,value)
    -------------------------------------------------------
    Parameters:
        device_name - the device name/address (str)
        value - a float value for temperature (float)
    Returns:
        value - a float value for temperature (float)
    -------------------------------------------------------
    """
	if name == '9e0f':
		temp_c += 0.567
	elif name == '1e37':
		pass	
	elif name == '839e':
		temp_c -= 0.29	
	elif name == '4ee6':
		temp_c += 0.35		
	elif name == '071a':
		temp_c += 0.552
	elif name == '7b72':
		temp_c -= 0.045	
	elif name == 'd995':
		temp_c -= 0.165	
	elif name == 'f5d6':
		temp_c += 0.045	
	elif name == 'f969':
		temp_c -= 0.636	
	elif name == '1a77':
		temp_c += 0.142
	return temp_c