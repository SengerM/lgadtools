import numpy as np
import numbers

class LGADSignal:
	def __init__(self, time, samples):
		self.t = time
		self.s = samples
	
	def linearly_interpolated_val(self, t):
		if isinstance(t, numbers.Number):
			if t < min(self.t) or t > max(self.t):
				raise ValueError('"t" is outside the valid data range')
			prev_t_data_index = np.where(self.t <= t)[-1][-1]
			if prev_t_data_index == len(self.t)-1:
				return self.s[-1]
			slope = (self.s[prev_t_data_index+1] - self.s[prev_t_data_index])/(self.t[prev_t_data_index+1] - self.t[prev_t_data_index])
			return (t-self.t[prev_t_data_index])*slope + self.s[prev_t_data_index]
		elif hasattr(t, '__iter__'):
			return [self.linearly_interpolated_val(t_val) for t_val in t]
		else:
			raise ValueError('"t" must be a number or an iterable of numbers')
	
	def _find_baseline(self, sigmas=1):
		for k, sample in enumerate(self.s):
			if k < 9:
				continue
			baseline = self.s[:k+1].mean()
			if sample > baseline + sigmas*self.s[:k+1].std() or sample < baseline - sigmas*self.s[:k+1].std():
				break
		return baseline
	
	def _find_noise_std(self):
		return self.s[:self.rise_window_indices[0]].std()
	
	@property
	def noise_std(self):
		if hasattr(self, 'noise_std_value'):
			return self.noise_std_value
		else:
			self.noise_std_value = self._find_noise_std()
			return self.noise_std
	
	@property
	def SNR(self):
		return self.amplitude/self.noise_std
	
	@property
	def baseline(self):
		if hasattr(self, 'baseline_value'):
			return self.baseline_value
		else:
			self.baseline_value = self._find_baseline(sigmas = 5)
			return self.baseline
	
	def _find_baseline_amplitude(self):
		return max(np.abs(self.s - self.baseline))
	
	@property
	def amplitude(self):
		if hasattr(self, 'amplitude_value'):
			return self.amplitude_value
		else:
			self.amplitude_value = self._find_baseline_amplitude()
			return self.amplitude
	
	def _find_rise_window(self, low=10, high=90):
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
	
	@property
	def risetime(self):
		if hasattr(self, 'risetime_value'):
			return self.risetime_value
		else:
			k_start, k_stop = self.rise_window_indices
			self.risetime_value = self.t[k_stop] - self.t[k_start]
			return self.risetime
	
	@property
	def rise_window_indices(self):
		if hasattr(self, 'k_start_rise') and hasattr(self, 'k_stop_rise'):
			return (self.k_start_rise, self.k_stop_rise)
		else:
			k_start, k_stop = self._find_rise_window()
			self.k_start_rise = k_start
			self.k_stop_rise = k_stop
			return self.rise_window_indices
