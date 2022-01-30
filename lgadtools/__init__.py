import warnings

name = "lgadtools"

# Numerical version:
__version_info__ = (1, 0, 0)
__version__ = '.'.join(map(str, __version_info__))

__author__ = 'Matias H. Senger <m.senger@hotmail.com>'

warnings.warn(f'DEPRECATION WARNING: The `lgadtools` package is deprecated, consider using the `signals` package located here: https://github.com/SengerM/signals')
