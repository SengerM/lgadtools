import numpy as np
import numbers
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from scipy import interpolate

class Signal:
	# Implements a signal that was sampled.
	def __init__(self, time, samples):
		if type(time) == list:
			time = np.array(time)
		if type(samples) == list:
			samples = np.array(samples)
		self.time = time
		self.samples = samples
	
	@property
	def t(self):
		# Returns the time samples.
		return self.time
	
	@property
	def s(self):
		# Returns the signal samples.
		return self.samples
	
	def signal_at(self, time):
		# Returns the value of the signal at any time using a linear interpolation.
		return interpolate.interp1d(self.t, self.s)(time)

class LGADSignal(Signal):
	# Adapts the "Signal" class to signals that have the shape of that comming out
	# from an LGAD detector, i.e. a pulse.
	@property
	def s_norm(self):
		# Returns the samples normalized between 0 and 1.
		if hasattr(self, '_s_norm'):
			return self._s_norm
		else:
			self._s_norm = (self.s - self.baseline)/self.amplitude
			return self.s_norm
	
	def _find_baseline(self, sigmas=1):
		# Calculates the baseline. This method is not intended to be called by the user.
		for k, sample in enumerate(self.s):
			if k < 9:
				continue
			baseline = self.s[:k+1].mean()
			if sample > baseline + sigmas*self.s[:k+1].std() or sample < baseline - sigmas*self.s[:k+1].std():
				break
		return baseline
	
	def _find_noise_std(self):
		# Calculates the noise. This method is not intended to be called by the user. 
		return self.s[:self.rise_window_indices[0]].std()
	
	@property
	def noise_std(self):
		# Returns the noise standard deviation.
		if hasattr(self, 'noise_std_value'):
			return self.noise_std_value
		else:
			self.noise_std_value = self._find_noise_std()
			return self.noise_std
	
	@property
	def SNR(self):
		# Returns the signal to noise ratio.
		return self.amplitude/self.noise_std
	
	@property
	def baseline(self):
		# Returns the baseline.
		if hasattr(self, 'baseline_value'):
			return self.baseline_value
		else:
			self.baseline_value = self._find_baseline(sigmas = 5)
			return self.baseline
	
	def _find_baseline_amplitude(self):
		return max(np.abs(self.s - self.baseline))
	
	@property
	def amplitude(self):
		# Returns the amplitude of the signal.
		if hasattr(self, 'amplitude_value'):
			return self.amplitude_value
		else:
			self.amplitude_value = self._find_baseline_amplitude()
			return self.amplitude
	
	def _find_rise_window_indices(self, low=10, high=90):
		# Finds the two indices such that the signal rises between these two indices. This method is not intended to be called by the user.
		below_low = self.s < low/100*self.amplitude + self.baseline
		above_high = self.s > high/100*self.amplitude + self.baseline
		between = (self.s > low/100*self.amplitude + self.baseline) & (self.s < high/100*self.amplitude + self.baseline)
		
		rising_from_low = False
		rising_to_high = False
		for k in range(len(self.s)):
			if not between[k]:
				rising_from_low = False
				rising_to_high = False
				continue
			if not between[k-1] and below_low[k-1]:
				rising_from_low = True
				k_start_rise = k
			if not between[k+1] and above_high[k+1]:
				rising_to_high = True
				k_stop_rise = k
			if rising_from_low and rising_to_high:
				return k_start_rise, k_stop_rise
	
	def time_at(self, percentage):
		# Returns the time at <percentage> in the rising window using linear interpolation between the points.
		_min_perc = 10
		_max_perc = 100
		if not _min_perc <= percentage <= _max_perc:
			raise ValueError('<percentage> must be between ' + str(_min_perc) + ' and ' + str(_max_perc) + ', received ' + str(percentage))
		time_vs_voltage_in_rise_window = interpolate.interp1d(
			x = self.s[self.rise_window_indices[0]:np.argmax(self.s)],
			y = self.t[self.rise_window_indices[0]:np.argmax(self.s)],
		)
		return time_vs_voltage_in_rise_window(self.amplitude*percentage/100 + self.baseline)
	
	@property
	def risetime(self):
		# Returns the risetime.
		if hasattr(self, 'risetime_value'):
			return self.risetime_value
		else:
			try:
				self.risetime_value = self.rise_window_times[1] - self.rise_window_times[0]
				return self.risetime
			except TypeError:
				return None
	
	@property
	def rise_window_times(self):
		# Returns t_start and t_stop at which the signal starts to rise and stops to rise.
		if hasattr(self, 'rise_window_time_value'):
			return self.rise_window_time_value
		else:
			try:
				k_start, k_stop = self.rise_window_indices
				slope = (self.t[k_start]-self.t[k_start-1])/(self.s[k_start]-self.s[k_start-1])
				t_start_rise = self.t[k_start-1] + (.1*self.amplitude - self.s[k_start-1])*slope
				slope = (self.t[k_stop+1]-self.t[k_stop])/(self.s[k_stop+1]-self.s[k_stop])
				t_stop_rise = self.t[k_stop] + (.9*self.amplitude - self.s[k_stop])*slope
				self.rise_window_time_value = (t_start_rise, t_stop_rise)
				return self.rise_window_times
			except TypeError:
				print('WARNING: cannot find rise window times')
	
	@property
	def rise_window_indices(self):
		# Returns the indices k_start and k_stop where the signal rises.
		if hasattr(self, 'k_start_rise') and hasattr(self, 'k_stop_rise'):
			return (self.k_start_rise, self.k_stop_rise)
		else:
			try:
				k_start, k_stop = self._find_rise_window_indices()
				self.k_start_rise = k_start
				self.k_stop_rise = k_stop
				return self.rise_window_indices
			except TypeError:
				print('WARNING: cannot find rise window indices')
	
	def plot(self, ax, *args, **kwargs):
		# Plots the signal.
		_fig, _ax = plt.subplots()
		if type(ax) == type(_ax):
			ax.plot(
				self.t,
				self.s,
				*args,
				**kwargs
			)
		else:
			raise TypeError('The "ax" argument must be an instance of type ' + str(type(_ax)))
		plt.close(_fig)
		del(_fig)
		del(_ax)
	
	def plot_with_analysis(self, ax):
		plot_signal_analysis(self, ax)
		

def plot_signal_analysis(signal: LGADSignal, ax):
	ax.plot(
		signal.t,
		signal.s,
		marker = '.'
	)
	ax.plot(
		[min(signal.t), max(signal.t)],
		[signal.baseline, signal.baseline],
		label = 'baseline'
	)
	ax.plot(
		[min(signal.t), max(signal.t)],
		[signal.baseline + signal.noise_std, signal.baseline + signal.noise_std],
		label = 'noise std',
		color = (0,0,0),
		linestyle = '--'
	)
	ax.plot(
		[min(signal.t), max(signal.t)],
		[signal.baseline - signal.noise_std, signal.baseline - signal.noise_std],
		color = (0,0,0),
		linestyle = '--'
	)
	ax.plot(
		[min(signal.t), max(signal.t)],
		[signal.amplitude + signal.baseline, signal.amplitude + signal.baseline],
		label = 'amplitude + baseline'
	)
	rise_window_rectangle = patches.Rectangle(
		(
			signal.rise_window_times[0], 
			signal.baseline + .1*signal.amplitude
		),
		signal.risetime,
		.8*signal.amplitude,
		alpha = .3,
		color = (0,0,0)
	)
	ax.add_patch(rise_window_rectangle)
	ax.set_xlabel('Time (s)')
	ax.set_ylabel('Signal (V)')
	ax.legend()
