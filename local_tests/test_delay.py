import numpy as np
import matplotlib.pyplot as plt

time_around_pulse_ms = 50

chan = (-8, -4)
low, high = chan
freq = np.linspace(-10, 10, 1024)

idx0 = np.argmin(np.abs(freq - low)) # Time index gotten by multiplying by 0.5ms
idx1 = np.argmin(np.abs(freq - high))

idx0 = idx0*0.5 - time_around_pulse_ms//2
idx1 = idx1*0.5 + time_around_pulse_ms//2

delays = np.arange(idx0, idx1 + 1, 0.5) # Delays of pulse in ms

delays_array = np.zeros((len(delays), len(freq)))

for i in range(len(delays)):
    print(delays[i])
    delays_array[i, :] = np.arange(len(freq))*0.5-delays[i]*10


plt.imshow(delays_array, cmap='turbo')
plt.show()
