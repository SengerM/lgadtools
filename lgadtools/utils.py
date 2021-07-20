from scipy.stats import gaussian_kde
from scipy.optimize import minimize
import numpy as np

def most_probable_value(samples):
	"""Estimates the most probable value for the underlying distribution
	that produced the samples using a Gaussian KDE estimation for the
	distribution function.
	samples: An array with the samples.
	returns: A float number with the most probable value."""
	return minimize(
		lambda x: -gaussian_kde(samples)(x), 
		x0 = np.nanmean(samples),
		method = 'nelder-mead',
		options = {'xatol': 1e-8}
	).x[0]
	
def estimate_collected_charge_from_samples(samples):
	"""Estimates the collected charge from a collection of samples as the
	most probable value of the underlying distribution."""
	return most_probable_value(samples)
