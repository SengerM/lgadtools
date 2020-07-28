# lgadtools

Some stuff for the LGAD detectors.

## Installation

To make this work, you must install

1. This Python package:
	```
	pip3 install git+https://github.com/SengerM/lgadtools
	```

2. Install [Root 6](https://ph-root-2.cern.ch/).

3. Install the [TCTAnalyse](http://particulars.si/TCTAnalyse/) library from [Particulars](http://particulars.si/). If you are using Linux please install it in ```~/.TCTAnalyse.V2.2/TCTAnalyse.sl```. If you are not using Linux, or you want to install it in another location, then you must manually load the library after you import this Python package. Examples:

  - If you use Linux and have installed the library at ```~/.TCTAnalyse.V2.2/TCTAnalyse.sl``` then on Python:
  ```
  from lgadtools import TCTAnalyse
  ```
  
  - If your library is not at ```~/.TCTAnalyse.V2.2/TCTAnalyse.sl``` then on Python:
  ```
  from lgadtools import TCTAnalyse # This will print a horrible error, don't care.
  TCTAnalyse.load_TCTAnalyse(path = 'path/to/your/TCTAnalyse.dll')
  ```

Once you have installed all the previous stuff, 

## Usage

```
from lgadtools import TCTAnalyse
import matplotlib.pyplot as plt

stct = TCTAnalyse.PSTCT('path/to/binary/file/produced/by/TCT_software')

signal = stct.GetWF(y=1) # Get the sinal from the y=1 step.
print(signal.amplitude)
print(signal.noise)
print(signal.risetime)
print(signal.t) # Time samples.
print(signal.s) # Signal samples.

fig, ax = plt.subplots()
signal.plot(ax) # Plot the signal.
plt.show()
```
