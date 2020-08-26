import os
import numpy as np
from .LGADSignal import LGADSignal
import matplotlib.pyplot as plt

class CoincidenceTrigger:
	def __init__(self, trigger_number: int, S1: LGADSignal, S2: LGADSignal):
		self.trigger_number = trigger_number
		self.S1 = S1
		self.S2 = S2
	
	def __getitem__(self, key):
		if isinstance(key, int):
			if key == 1:
				return self.S1
			elif key == 2:
				return self.S2
			else: 
				raise KeyError('If you pass an integer it must be 1 or 2')
		elif isinstance(key, str):
			if key[-1] == '1':
				return self.S1
			elif key[-1] == '2':
				return self.S2
			elif key.lower() == 'trigger number':
				return self.trigger_number
			else:
				raise KeyError('If you specify a string it must end either in 1 or 2 or be "trigger number"')
		else:
			raise KeyError('The "key" must be either an int or a string')

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
	def __init__(self, path_to_measurement_directory):
		if path_to_measurement_directory[-1] == '/':
			path_to_measurement_directory = path_to_measurement_directory[:-1]
		self.path_to_measurement_directory = path_to_measurement_directory
	
	@property
	def raw_data_dir(self):
		if 'raw data' not in os.listdir(self.path_to_measurement_directory):
			raise ValueError('There is no "raw data" directory in "' + self.path_to_measurement_directory + '"')
		return self.path_to_measurement_directory + '/raw data'
	
	@property
	def processed_data_dir(self):
		if 'processed data' not in os.listdir(self.path_to_measurement_directory):
			os.mkdir(self.path_to_measurement_directory + '/processed data')
		return self.path_to_measurement_directory + '/processed data'
	
	@property
	def parsed_signal_attributes_file_path(self):
		return self.processed_data_dir + '/parsed signal attributes.txt'
	
	def save_parsed_attributes_individual_signals(self, triggers):
		with open(self.parsed_signal_attributes_file_path, 'w') as ofile:
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
	
	def read_raw_data(self, trigger_numbers = []):
		return read_coincidence_waveforms_Lecroy_WaveRunner_9254M(self.raw_data_dir, trigger_numbers)

	def verbose_plot_raw_data(self, trigger: CoincidenceTrigger):
		fig, ax = plt.subplots()
		for sensor in ['Sensor 1', 'Sensor 2']:
			ax.plot(
				trigger[sensor].t,
				trigger[sensor].s,
				label = sensor,
			)
			ax.set_xlabel('Time (s)')
			ax.set_ylabel('Amplitude (V)')
		plt.show()
