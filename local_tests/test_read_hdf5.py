from HDF5_BLS import Wrapper
import matplotlib.pyplot as plt 
import numpy as np

filepath = "/Users/pierrebouvet/Desktop/test.h5"

wrp = Wrapper(filepath)
 
delays = wrp['Brillouin/Test/Abscissa']
freq = wrp['Brillouin/Test/Frequency']
psd = wrp['Brillouin/Test/PSD']

channels = np.tile(freq[np.newaxis, :], (delays.shape[0], 1))
plt.pcolormesh(delays, channels, psd)
plt.xlabel("Delay from pulse (ms)")
plt.ylabel("Frequency shift(GHz)")
plt.show()
