import numpy as np

freq = np.linspace(-10, 10, 1024)
chosen_freq = [-6, -3]


chosen_freq_idx = np.where((freq>=chosen_freq[0]) & (freq<=chosen_freq[1]))

print(chosen_freq_idx)