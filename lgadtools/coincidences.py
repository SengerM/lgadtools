import os
import numpy as np
from .LGADSignal import LGADSignal
import matplotlib.pyplot as plt
import yaml

__METADATA_FILE_TEMPLATE__ = '''Name: <Name of the measurement> (e.g. The best LGAD detectors you have seen

Description: <Some comment on your measurement> (e.g. Today it was raining and the humidity was too high)

Devices: (List the devices in ascending order of oscilloscope channel number)
  <Device 1 name> (e.g. W3-DB19):
    Bias voltage: <voltage> (e.g. 90 V)
    Connected to oscilloscope: <channel> (e.g. CH2)
    (Add your own fields here)
  
  <Device 1 name> (e.g. W3-DB31):
    Bias voltage: <voltage> (e.g. 80 V)
    Connected to oscilloscope: <channel> (e.g. CH3)
    (Add your own fields here)
'''

class Sensor1Sensor2StuffContainer:
	def __init__(self, S1_stuff, S2_stuff):
		self.S1_stuff = S1_stuff
		self.S2_stuff = S2_stuff
	
	def __getitem__(self, key):
		if isinstance(key, int):
			if key == 0:
				return self.S1_stuff
			elif key == 1:
				return self.S2_stuff
			else: 
				raise KeyError('If you pass an integer it must be 0 or 1')
		elif isinstance(key, str):
			if '1' in key:
				return self.S1_stuff
			elif '2' in key:
				return self.S2_stuff
			else:
				raise KeyError('If you specify a string it must have either in "1" or "2" within it')
		else:
			raise KeyError('The "key" must be either an int or a string')
	
	def __str__(self):
		return '[1: ' + str(self.S1_stuff) + ', 2: ' + str(self.S2_stuff) + ']'

class CoincidenceTrigger:
	def __init__(self, trigger_number: int, S1: LGADSignal, S2: LGADSignal):
		self.trigger_number = trigger_number
		self.signals = Sensor1Sensor2StuffContainer(S1, S2)
	
	def __getitem__(self, key):
		if key.lower() in ['trigger number', 'number']: #
			return self.trigger_number
		else:
			return self.signals[key]
	
	@property
	def ugly(self):
		return not (self.signals[0].worth and self.signals[1].worth)
	
	def verbose_plot(self, fig = None):
		if fig == None:
			fig, ax = plt.subplots()
			for sensor in ['Sensor 1', 'Sensor 2']:
				ax.plot(
					self.signals[sensor].t,
					self.signals[sensor].s,
					label = sensor,
				)
				ax.set_xlabel('Time (s)')
				ax.set_ylabel('Amplitude (V)')
				ax.legend()
				fig.suptitle('Trigger ' + str(self.trigger_number))
			plt.show()
		else: # Assuming a "myplotlib" fig object. See https://github.com/SengerM/myplotlib.
			for sensor in ['Sensor 1', 'Sensor 2']:
				fig.plot(
					self.signals[sensor].t,
					self.signals[sensor].s,
					label = sensor,
				)
			fig.set(
				xlabel = 'Time (s)',
				ylabel = 'Amplitude (V)',
				title = 'Trigger ' + str(self.trigger_number)
			)

def read_coincidence_waveforms_Lecroy_WaveRunner_9254M(directory: str, trigger_numbers = []):
	# C2--Trace--00106.txt
	triggers = []
	fnames = sorted(os.listdir(directory))
	if trigger_numbers == []:
		for fname in fnames:
			if '--Trace--' not in fname or len(fname) != 20:
				continue
			trig_number = int(fname[-9:-4])
			if trig_number in trigger_numbers:
				continue
			if f'C2--Trace--{trig_number:05}.txt' not in fnames or f'C3--Trace--{trig_number:05}.txt' not in fnames:
				print('Skipping file "' + fname + '" because there is no "partner trigger" with the same number and the other channel')
				continue
			trigger_numbers.append(trig_number)
	
	for trigNmbr in trigger_numbers:
		fname = f'C2--Trace--{trigNmbr:05}.txt'
		data = np.genfromtxt(
			fname = directory + '/' + fname,
			skip_header = 5,
			delimiter = ',',
		).transpose()
		s1 = LGADSignal(
			time = data[0],
			samples = data[1]
		)
		fname = f'C3--Trace--{trigNmbr:05}.txt'
		data = np.genfromtxt(
			fname = directory + '/' + fname,
			skip_header = 5,
			delimiter = ',',
		).transpose()
		s2 = LGADSignal(
			time = data[0],
			samples = data[1]
		)
		triggers.append(
			CoincidenceTrigger(
				S1 = s1, 
				S2 = s2,
				trigger_number = trigNmbr,
			)
		)
	return triggers

class CoincidenceMeasurementBureaucrat:
	def __init__(self, path_to_measurement_directory=None):
		if path_to_measurement_directory == None: # Assume we are working inside the "scripts" directory of an existing measurement and get it directly.
			path_to_measurement_directory = os.getcwd().replace('/scripts', '')
			if not os.path.isdir(path_to_measurement_directory):
				raise ValueError('You did not specified a <path_to_measurement_directory> and I assumed you were working inside the "scripts" directory of an existing measurement, but this is not the case... Please check.')
		if not isinstance(path_to_measurement_directory, str):
			raise TypeError('<path_to_measurement_directory> must be a string')
		if path_to_measurement_directory[-1] == '/':
			path_to_measurement_directory = path_to_measurement_directory[:-1]
		if not os.path.isdir(path_to_measurement_directory):
			raise ValueError('The directory you provided in <path_to_measurement_directory> is not a directory.')
		self.path_to_measurement_directory = path_to_measurement_directory
	
	@property
	def raw_data_dir(self):
		return self.path_to_measurement_directory + '/data/raw'
	
	@property
	def processed_data_dir(self):
		return self.path_to_measurement_directory + '/data/processed'
	
	@property
	def parsed_attributes_individual_signals_file_path(self):
		return self.processed_data_dir + '/parsed signal attributes.txt'
	
	@property
	def nice_trigger_numbers_list_file_path(self):
		return self.processed_data_dir + '/nice trigger numbers list.txt'
	
	@property
	def scripts_dir(self):
		return self.path_to_measurement_directory + '/scripts'
	
	@property
	def pics_dir(self):
		return self.path_to_measurement_directory + '/pics'
	
	def save_nice_trigger_numbers_list(self, trigger_numbers: list):
		with open(self.nice_trigger_numbers_list_file_path, 'w') as ofile:
			print('# List of "nice trigger numbers" obtained after throwing away garbage triggers.', file = ofile)
			for t in trigger_numbers:
				print(t, file = ofile)
	
	def read_nice_trigger_numbers_list_file(self):
		trigs = []
		with open(self.nice_trigger_numbers_list_file_path, 'r') as ifile:
			for line in ifile:
				if line[0] == '#':
					continue
				trigs.append(int(line))
		return trigs
	
	def save_parsed_attributes_individual_signals(self, triggers):
		with open(self.parsed_attributes_individual_signals_file_path, 'w') as ofile:
			print('# Trigger number\tAmplitude S1 (V)\tNoise RMS S1 (V)\tRisetime S1 (s)\tAmplitude S2 (V)\tNoise RMS S2 (V)\tRisetime S2 (s)', file = ofile)
			for trig in triggers:
				line = str(trig['trigger number'])
				line += '\t'
				for s in ['sensor 1', 'sensor 2']:
					try:
						line += str(trig[s].amplitude)
						line += '\t'
						line += str(trig[s].noise_std)
						line += '\t'
						line += str(trig[s].risetime)
						line += '\t'
					except:
						raise ValueError('I cannot calculate the parameters of the signal for ' + s + ' in trigger number ' + str(trig['trigger number']) + ' because it might be a crappy one or just Wi-Fi noise. Plot it and check, please...')
				line = line[:-1]
				print(line, file = ofile)
	
	def read_parsed_attributes_individual_signals(self):
		try:
			data = np.genfromtxt(self.parsed_attributes_individual_signals_file_path).transpose()
		except OSError:
			raise OSError('File ' + self.parsed_attributes_individual_signals_file_path + ' cannot be opened. Before attempting to read the parsed attributes you must save them!')
		return {
			'trigger numbers': data[0].astype(np.int),
			'amplitudes': Sensor1Sensor2StuffContainer(data[1],data[4]),
			'noises': Sensor1Sensor2StuffContainer(data[2],data[5]),
			'risetimes': Sensor1Sensor2StuffContainer(data[3],data[6]),
		}
		
	
	def read_raw_data(self, trigger_numbers = []):
		if isinstance(trigger_numbers, int):
			return self.read_raw_data([trigger_numbers])
		return read_coincidence_waveforms_Lecroy_WaveRunner_9254M(self.raw_data_dir, trigger_numbers)
	
	@property
	def metadata_file_path(self):
		return self.path_to_measurement_directory + '/metadata.yaml'
	
	def read_metadata_file(self):
		try:
			with open(self.metadata_file_path) as ifile:
				metadata = yaml.safe_load(ifile)
		except FileNotFoundError:
			raise FileNotFoundError('There is no "metadata.yaml" file in ' + self.path_to_measurement_directory)
		return metadata
	
	@property
	def devices_names(self):
		if hasattr(self, '__devices_names'):
			return self.__devices_names
		else:
			metadata_file_exists = True
			try:
				metadata = self.read_metadata_file()
			except FileNotFoundError:
				metadata_file_exists = False
			if metadata_file_exists == False or metadata.get('Devices') == None:
				return Sensor1Sensor2StuffContainer('Unknown', 'Unknown')
			else:
				self.__devices_names = Sensor1Sensor2StuffContainer(list(metadata['Devices'].keys())[0], list(metadata['Devices'].keys())[1])
				return self.__devices_names
	
	@property
	def measurement_name(self):
		if hasattr(self, '__measurement_name'):
			return self.__measurement_name
		else:
			name = self.read_metadata_file().get('Name')
			self.__measurement_name = name if name != None else 'Unknown'
			return self.__measurement_name
	
	def print_metadata_file_template(self):
		print(__METADATA_FILE_TEMPLATE__)
	
	def CFD_time_delta_file_path(self, CFD: int):
		if not isinstance(CFD, int) and not 0 < CFD < 99:
			raise ValueError('<CFD> must be an integer number bounded between 0 and 99')
		return self.processed_data_dir + f'/time deltas at CFD files/CFD {CFD:02} %.txt'
	
	def save_CFD_time_delta_file(self, CFD: int, time_deltas: list):
		with open(self.CFD_time_delta_file_path, 'w') as ofile:
			print(f'# Time deltas at CFD = {CFD:02} % for measurement "' + self.measurement_name + '"', file = ofile)
			for Dt in time_deltas:
				print(Dt, file = ofile)
