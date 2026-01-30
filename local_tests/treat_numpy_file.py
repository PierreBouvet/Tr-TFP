import numpy as np 
import matplotlib.pyplot as plt
from HDF5_BLS_treat import Treat

# Extract results
source_filepath = '/Volumes/LAUDATE/Data/260100 - TR-TFP/Salted Water - 10ms pulse 1mA - unipolar - -10 300 - -7 100-3mm-150nm.npy'
results = np.load(source_filepath)

plt.figure()
plt.imshow(results, aspect='auto', extent = [0, results.shape[1]*0.5, 0, results.shape[0]])
plt.xlabel("Time axis normalized on delay (ms)")
plt.ylabel("Replication of the measure \nat different delays")

# Compute frequency axis
c = 299792458
laser_wavelength = 532
mirror_spacing = 3
scanning_range = 150
nb_samples = 1024

FSR_Hz = c/(2*mirror_spacing*1e-3) # From TFP manual
range_Hz = 2*scanning_range / laser_wavelength * FSR_Hz # From TFP manual
freq_axis_func = lambda nb_samples: np.linspace(-range_Hz/2, range_Hz/2, nb_samples)
freq = freq_axis_func(nb_samples)

# Get observed window
f_min = -10300000000
f_max = -7100000000

# # f_min, f_max = -f_min, -f_max

poss = [np.argmin(np.abs(freq - f_min)), np.argmin(np.abs(freq - f_max))]
pos_min = min(poss)
pos_max = max(poss)

# pos_min = 172
# pos_max = 322

dt_ms = 50
pos_min = min(poss)#+2*dt_ms
pos_max = max(poss)#+2*dt_ms

pos_pulse = (pos_max+pos_min)//2 + dt_ms/0.5
plt.vlines(pos_pulse*0.5, 0, results.shape[0], colors='r')

print(results.shape)
print(dt_ms/0.5, pos_max-pos_min)

spectra = []
# for i in range(dt_ms/0.5, )

# plt.figure()
# plt.plot(freq, results[0, :1024])
# plt.plot(freq, results[-1, :1024])
# plt.vlines(freq[pos_min], 0, np.max(results[-1, :1024]), colors='g')
# plt.vlines(freq[pos_max], 0, np.max(results[-1, :1024]), colors='g')


# # Extract region of stimulation
# N = results.shape[0]
# stimulation_region = np.zeros((N, pos_max-pos_min))
# for i in range(N):
#     stimulation_region[i, :] = results[i, N-i+pos_min:N-i+pos_max]
# freq_stimul_region = freq[pos_min:pos_max]
# dt = np.linspace(-N*0.25, N*0.25, N)

# freq_stimul_region = freq_stimul_region*1e-9

# plt.figure()
# plt.imshow(stimulation_region, aspect='auto', extent=[freq_stimul_region[0], freq_stimul_region[-1], dt[0], dt[-1]])
# plt.xlabel("Frequency shift (GHz)")
# plt.ylabel("Delay from pulse (ms)")

# # Treat

# x0 = -8.7
# dx = 1

# # Initialising the Treat object on the a doublet of frequency and PSD
# treat = Treat(frequency = freq_stimul_region, PSD = stimulation_region)

# # Creating a blank algorithm to perform the analysis
# treat.silent_create_algorithm(algorithm_name="VIPA spectrum analyser", 
#                         version="v0", 
#                         author="Pierre Bouvet", 
#                         description="This algorithm allows the user to recover a frequency axis basing ourselves on a single Brillouin spectrum obtained with a VIPA spectrometer. Considering that only one Brillouin Stokes and anti-Stokes doublet is visible on the spectrum, the user can select the peaks he sees, and then perform a quadratic interpolation to obtain the frequency axis. This interpolation is obtained either by entering a value for the Brillouin shift of the material or by entering the value of the Free Spectral Range (FSR) of the spectrometer. The user can finally recenter the spectrum either using the average between a Stokes and an anti-Stokes peak or by choosing an elastic peak as zero frequency.")

# # Adding points corresponding to the central peaks to the algorithm so as to normalize the PSD
# treat.add_point(position_center_window=x0, type_pnt="Stokes", window_width=2)
# # treat.add_point(position_center_window=5, type_pnt="Stokes", window_width=2)
# treat.normalize_data(threshold_noise = 0.05)

# # Adding the peaks to fit
# treat.add_point(position_center_window=x0, type_pnt="Stokes", window_width=2)
# # treat.add_point(position_center_window=5, type_pnt="Stokes", window_width=2)

# # Defining the model for fitting the peaks
# treat.define_model(model="DHO", elastic_correction=False) 

# # Estimating the linewidth from selected peaks
# treat.estimate_width_inelastic_peaks(max_width_guess=5)

# # Fitting all the selected inelastic peaks with multiple peaks fitting
# treat.single_fit_all_inelastic(guess_offset=True, 
#                                 update_point_position=True, 
#                                 bound_shift=[[x0-dx, x0+dx]], 
#                                 bound_linewidth=[[0, 2]])
# # treat.single_fit_all_inelastic(guess_offset=True, 
# #                                 update_point_position=True, 
# #                                 bound_shift=[[4, 6]], 
# #                                 bound_linewidth=[[0, 2]])


# # Applying the algorithm to all the spectra (in the case where PSD is a 2D array)
# treat.apply_algorithm_on_all()

# shift = treat.shift
# linewidth = treat.linewidth

# plt.figure()
# plt.subplot(211)
# plt.plot(dt, shift)
# plt.xlabel("Delay from pulse (ms)")
# plt.ylabel("Frequency shift (Hz)")
# plt.subplot(212)
# plt.plot(dt, linewidth)
# plt.xlabel("Delay from pulse (ms)")
# plt.ylabel("Linewidth (Hz)")


plt.show()
