import numpy as np
from scipy import interpolate, integrate

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
	# It is assumed that the pulse is positive.
	#
	# DESIGN RULES
	# ------------
	# 
	# - Methods of type <@property> do not raise any error. They return
	#   the corresponding value or float('NaN') or whatever, but NO ERRORS!
	# - Methods of type <@property> store calculated values in memory in
	#   order to increase processing speed. <find_...> methods do not
	#   store anything, they do the required processing each time they
	#   are called.
	# - Methods of type <@property> call methods of type <find_...> where
	#   the actual calculation/processing is done. These <find_...> methods
	#   do raise errors if they consider it necessary.
	
	# @property methods ------------------------------------------------
	
	@property
	def baseline(self):
		if hasattr(self, '_baseline'):
			return self._baseline
		else:
			try:
				self._baseline = self.find_baseline()
			except:
				self._baseline = float('NaN')
			return self._baseline
	
	@property
	def amplitude(self):
		if hasattr(self, '_amplitude'):
			return self._amplitude
		else:
			try:
				self._amplitude = self.find_amplitude()
			except:
				self._amplitude = float('NaN')
			return self._amplitude
	
	@property
	def noise(self):
		if hasattr(self, '_noise'):
			return self._noise
		else:
			try:
				self._noise = self.find_noise()
			except:
				self._noise = float('NaN')
			return self._noise
	
	@property
	def SNR(self):
		try:
			snr = self.amplitude/self.noise
		except:
			snr = float('NaN')
		return snr
	
	@property
	def rise_time(self):
		if hasattr(self, '_rise_time'):
			return self._rise_time
		else:
			try:
				self._rise_time = self.find_time_at_rising_edge(90) - self.find_time_at_rising_edge(10)
			except:
				self._rise_time = float('NaN')
			return self._rise_time
	
	@property
	def collected_charge(self):
		if hasattr(self, '_collected_charge'):
			return self._collected_charge
		else:
			try:
				self._collected_cahrge = self.calculate_collected_charge(R=1,threshold=self.noise/self.amplitude*100)[0]
			except:
				self._collected_charge = float('NaN')
			return self._collected_charge
	
	@property
	def rising_edge_indices(self):
		if hasattr(self, '_rising_edge_indices'):
			return self._rising_edge_indices
		else:
			try:
				self._rising_edge_indices = self.find_rising_edge_indices(low = 10, high = 90)
			except:
				self._rising_edge_indices = [float('NaN'), float('NaN')]
			return self._rising_edge_indices
	
	@property
	def falling_edge_indices(self):
		if hasattr(self, '_falling_edge_indices'):
			return self._falling_edge_indices
		else:
			try:
				self._falling_edge_indices = self.find_falling_edge_indices(low = 10, high = 90)
			except:
				self._falling_edge_indices = [float('NaN'), float('NaN')]
			return self._falling_edge_indices
	
	@property
	def time_over_noise(self):
		if hasattr(self, '_time_over_noise'):
			return self._time_over_noise
		else:
			try:
				self._time_over_noise = self.find_time_over_threshold(threshold = self.noise/self.amplitude*100)
			except:
				self._time_over_noise = float('NaN')
			return self._time_over_noise
	
	@property
	def collected_charge(self):
		if hasattr(self, '_collected_charge'):
			return self._collected_charge
		else:
			try:
				self._collected_charge = self.find_collected_charge(threshold = self.noise/self.amplitude*100)
			except:
				self._collected_charge = float('NaN')
			return self._collected_charge
	
	# find_ methods ----------------------------------------------------
	
	def find_baseline(self):
		return np.median(self.samples[:np.argmax(self.samples)])
	
	def find_amplitude(self):
		return max(self.samples - self.baseline)
	
	def find_noise(self):
		k_start = self.rising_edge_indices[0]
		if np.isnan(k_start):
			raise RuntimeError(f'Cannot determine the begining of the rising edge.')
		return self.samples[:k_start].std()
	
	def find_rising_edge_indices(self, low: float, high: float):
		# <low> and <high> are the percentage values to consider the rise window,
		# e.g. low = 10 (percent) and high = 90 (percent).
		low = float(low)
		high = float(high)
		if not low < high:
			raise ValueError(f'<low> must be less than <high>, received low={low} and high={high}.')
		k = self.samples.argmax()
		k_start_rise = None
		k_stop_rise = None
		while k > 0:
			if self.samples[k] - self.baseline > self.amplitude*high/100:
				k_stop_rise = k+1
			if self.samples[k] - self.baseline < self.amplitude*low/100:
				k_start_rise = k
				break
			k -= 1
		if k_start_rise is None or k_stop_rise is None or k_start_rise == k_stop_rise:
			raise RuntimeError(f'Cannot find the rising edge of this signal. It is possible that the signal is very noisy, but please check.')
		return [k for k in range(k_start_rise, k_stop_rise)]
	
	def find_falling_edge_indices(self, low: float, high: float):
		# <low> and <high> are the percentage values to consider the rise window,
		# e.g. low = 10 (percent) and high = 90 (percent).
		low = float(low)
		high = float(high)
		if not low < high:
			raise ValueError(f'<low> must be less than <high>, received low={low} and high={high}.')
		k = self.samples.argmax()
		k_start_fall = None
		k_stop_fall = None
		while k < len(self.samples):
			if self.samples[k] - self.baseline > self.amplitude*high/100:
				k_start_fall = k
			if self.samples[k] - self.baseline < self.amplitude*low/100:
				k_stop_fall = k + 1
				break
			k += 1
		if k_start_fall is None or k_stop_fall is None:
			raise RuntimeError(f'Cannot find the falling edge of this signal. It is possible that the signal is very noisy, but please check.')
		return [k for k in range(k_start_fall, k_stop_fall)]
	
	def find_time_at_rising_edge(self, threshold: float):
		# Returns the time at <threshold> in the rising edge using linear interpolation between the samples.
		threshold = float(threshold)
		_min_perc = 0
		_max_perc = 90
		if not _min_perc <= threshold <= _max_perc:
			raise ValueError('<threshold> must be between ' + str(_min_perc) + ' and ' + str(_max_perc) + ', received ' + str(threshold))
		if len(self.rising_edge_indices) == 2 and np.isnan(self.rising_edge_indices[0]) and np.isnan(self.rising_edge_indices[-1]):
			raise RuntimeError('Cannot find rising edge of the signal.')
		if 10 <= threshold <= 90:
			rising_edge_indices = self.rising_edge_indices
		else:
			rising_edge_indices = self.find_rising_edge_indices(low = min(threshold, 10), high = max(threshold, 90))
		time_vs_voltage_in_rising_edge = interpolate.interp1d(
			x = self.samples[rising_edge_indices],
			y = self.time[rising_edge_indices],
		)
		if np.isnan(self.amplitude):
			raise RuntimeError('Cannot find the amplitude of the signal.')
		if np.isnan(self.baseline):
			raise RuntimeError('Cannot find the baseline of the signal.')
		return time_vs_voltage_in_rising_edge(self.amplitude*threshold/100 + self.baseline)
	
	def find_time_at_falling_edge(self, threshold: float):
		# Returns the time at <threshold> in the rising edge using linear interpolation between the samples.
		threshold = float(threshold)
		_min_perc = 0
		_max_perc = 100
		if not _min_perc <= threshold <= _max_perc:
			raise ValueError('<threshold> must be between ' + str(_min_perc) + ' and ' + str(_max_perc) + ', received ' + str(threshold))
		if len(self.rising_edge_indices) == 2 and np.isnan(self.rising_edge_indices[0]) and np.isnan(self.rising_edge_indices[-1]):
			raise RuntimeError('Cannot find rising edge of the signal.')
		if 10 <= threshold <= 90:
			falling_edge_indices = self.falling_edge_indices
		else:
			falling_edge_indices = self.find_falling_edge_indices(low = min(threshold, 10), high = max(threshold, 90))
		time_vs_voltage_in_falling_edge = interpolate.interp1d(
			x = self.samples[falling_edge_indices],
			y = self.time[falling_edge_indices],
		)
		if np.isnan(self.amplitude):
			raise RuntimeError('Cannot find the amplitude of the signal.')
		if np.isnan(self.baseline):
			raise RuntimeError('Cannot find the baseline of the signal.')
		return time_vs_voltage_in_falling_edge(self.amplitude*threshold/100 + self.baseline)
	
	def find_indices_over_threshold(self, threshold: float):
		# Threshold is a percentage.
		threshold = float(threshold)
		if not 0 <= threshold <= 100:
			raise ValueError(f'<threshold> must be a percentage, i.e. a real number between 0 and 100. Received {threshold}.')
		v_threshold = self.baseline + threshold/100*self.amplitude
		if np.isnan(v_threshold):
			raise RuntimeError('Cannot calculate the threshold voltage for this signal because either the amplitude and/or the baseline cannot be calculated.')
		k_top = np.argmax(self.samples)
		k_start = k_top
		while k_start >= 0:
			if self.samples[k_start] < v_threshold:
				break
			k_start -= 1
		k_start += 1
		if k_start <= 0:
			raise RuntimeError('Cannot find the beginning of the pulse.')
		k_stop = k_top
		while k_stop < len(self.samples):
			if self.samples[k_stop] < v_threshold:
				break
			k_stop += 1
		if k_stop >= len(self.samples)-1:
			raise RuntimeError('Cannot find the end of the pulse.')
		if k_start == k_stop:
			raise RuntimeError('Cannot find the indices over threshold.')
		return [k for k in range(k_start, k_stop)]
	
	def find_over_threshold_times(self, threshold: float):
		# <threshold> is a percentage.
		threshold = float(threshold)
		if not 0 <= threshold <= 100:
			raise ValueError(f'<threshold> must be a percentage, i.e. a real number between 0 and 100. Received {threshold}.')
		t_start = self.find_time_at_rising_edge(threshold)
		t_stop = self.find_time_at_falling_edge(threshold)
		return t_start, t_stop
	
	def find_time_over_threshold(self, threshold=20):
		# Threshold is a percentage.
		tstart, tend = self.find_over_threshold_times(threshold=threshold)
		return tend-tstart
	
	def find_collected_charge(self, threshold: float):
		# Threshold: Which part of the signal do we consider for calculating the charge. It is a percentage, e.g. threshold = 10 %.
		threshold = float(threshold)
		t_start, t_stop = self.find_over_threshold_times(threshold=threshold)
		if np.isnan(self.baseline):
			raise RuntimeError('Cannot find the baseline for this signal.')
		Q, *_ = integrate.quad(lambda t: (self.signal_at(time=t)-self.baseline), t_start, t_stop)
		return Q
	
	# Other methods ----------------------------------------------------
	
	def plot_myplotlib(self, fig):
		# <fig> is a Figure object created with https://github.com/SengerM/myplotlib
		from myplotlib.figure import MPLFigure
		if not isinstance(fig, MPLFigure):
			raise TypeError(f'<fig> must be an instance of MPLFigure, received an instance of type {type(fig)}. See https://github.com/SengerM/myplotlib')
		fig.set(
			xlabel = 'Time (s)',
			ylabel = 'Amplitude (V)',
		)
		fig.plot(
			[min(self.t), max(self.t)],
			[self.baseline, self.baseline],
			label = f'Baseline ({self.baseline:.2e} V)',
			color = (0,0,0)
		)
		fig.plot(
			[min(self.t), max(self.t)] + [max(self.t)] + [max(self.t), min(self.t)],
			[self.baseline + self.noise, self.baseline + self.noise] + [float('NaN')] + [self.baseline - self.noise, self.baseline - self.noise],
			label = f'Noise ({self.noise:.2e} V)',
			color = (.6,)*3,
			linestyle = '--',
		)
		try:
			fig.plot(
				[self.t[np.argmax(self.s)-9],self.t[np.argmax(self.s)+9]] + 2*[self.t[np.argmax(self.s)]] + [self.t[np.argmax(self.s)-9],self.t[np.argmax(self.s)+9]],
				2*[self.baseline] + [self.baseline, self.baseline + self.amplitude] + 2*[self.baseline+self.amplitude],
				label = f'Amplitude ({self.amplitude:.2e} V)',
				color = (0,.6,0),
			)
		except:
			fig.plot(
				[self.t[np.argmax(self.s)]]*2,
				[self.baseline, self.baseline+self.amplitude],
				label = f'Amplitude ({self.amplitude:.2e} V)',
				color = (0,.6,0),
			)
		try:
			t_start_rise = self.find_time_at_rising_edge(threshold=10)
			fig.plot(
				[t_start_rise, t_start_rise+self.rise_time, t_start_rise+self.rise_time, t_start_rise, t_start_rise],
				self.baseline + np.array([self.amplitude*.1, self.amplitude*.1, self.amplitude*.9, self.amplitude*.9, self.amplitude*.1]),
				label = f'Rise time ({self.rise_time:.2e} s)',
				color = (1,0,0),
				alpha = .5,
				linestyle = '--',
			)
		except:
			pass
		try:
			threshold = 20
			t_start, t_stop = self.find_over_threshold_times(threshold)
			fig.plot(
				[t_start,t_stop],
				2*[self.baseline+threshold/100*self.amplitude],
				label = f'Time over {threshold} % ({t_stop-t_start:.2e} s)',
				linestyle = '--',
				color = (.8,.3,.8)
			)
		except:
			pass
		fig.plot(
			self.t,
			self.s,
			label = 'Signal',
			marker = '.',
			color = (.4,.5,.8),
		)
		# ~ fig.plot(
			# ~ self.t[self.rising_edge_indices],
			# ~ self.s[self.rising_edge_indices],
			# ~ label = 'Rising edge',
			# ~ color = (0,0,.3),
			# ~ marker = 'o',
		# ~ )
		# ~ fig.plot(
			# ~ self.t[self.falling_edge_indices],
			# ~ self.s[self.falling_edge_indices],
			# ~ label = 'Falling edge',
			# ~ color = (0,0,.1),
			# ~ marker = 'o',
		# ~ )
		try:
			t_start, t_stop = self.find_over_threshold_times(threshold = self.noise/self.amplitude*100)
			fig.plot(
				[t_start] + list(self.time[(self.time>t_start)&(self.time<t_stop)]) + [t_start + self.time_over_noise] + [t_stop,t_start] + [t_start],
				[self.signal_at(t_start)] + list(self.samples[(self.time>t_start)&(self.time<t_stop)]) + [self.signal_at(t_start + self.time_over_noise)] + 2*[self.baseline] + [self.signal_at(t_start)],
				label = f'Collected charge ({self.collected_charge:.2e} a.u.)',
				color = (1,0,0),
			)
		except:
			pass
