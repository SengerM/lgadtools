import os
import numpy as np
from lgadtools.LGADSignal import LGADSignal

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
			{
				'sensor 1': s1, 
				'sensor 2': s2,
				'trigger number': trigNmbr,
			}
		)
	return triggers
