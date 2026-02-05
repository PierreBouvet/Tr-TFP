from HDF5_BLS import Wrapper
import matplotlib.pyplot as plt 
import numpy as np
from HDF5_BLS_treat import Treat

filepath = '/Volumes/LAUDATE/Data/260100 - TR-TFP/Glycerol stimulation 100ms range 20ms pulse 100V.h5'

wrp = Wrapper(filepath)

# print(wrp)

path = "Brillouin/Measures 2"
attributes = wrp.get_attributes(path)

delays = wrp[path + '/Delays']
freq = wrp[path + '/Frequency']*1e-9
psd = wrp[path + '/PSD']

fmin, fmax = attributes['MEASURE.First_channel_(GHz)']*1e-9, attributes['MEASURE.Last_channel_(GHz)']*1e-9


freq_mask = np.where((freq >= fmin) & (freq <= fmax))[0]
psd = psd[:, freq_mask]
freq = freq[freq_mask]
delays = delays[:, freq_mask]

# channels = np.tile(freq[np.newaxis, :], (delays.shape[0], 1))
# plt.pcolormesh(delays, channels, psd)
# plt.xlabel("Delay from pulse (ms)")
# plt.ylabel("Frequency shift(GHz)")
# plt.show()

delay_min, delay_max = delays[-1, -1], delays[0, 0]
delay_tot = delay_max - delay_min   

delay_axis = np.arange(delay_min, delay_max+0.5, 0.5)
results = np.zeros((len(delay_axis), len(freq)))

for i in range(psd.shape[0]):
    for j in range(psd.shape[1]):
        delay = delays[i, j]
        if delay in delay_axis:
            pos_delay = np.where(delay_axis == delay)[0][0]
            results[pos_delay, j] = psd[i, j]

plt.imshow(results, aspect='auto', origin='lower', extent=[fmin, fmax, delay_min, delay_max])
plt.xlabel("Frequency shift(GHz)")
plt.ylabel("Delay from pulse (ms)")

x0 = [-15.7]
nature = ['Anti-Stokes']
dx=5
linewidth_max = 10

# Initialising the Treat object on the a doublet of frequency and PSD
treat = Treat(frequency = freq, PSD = results)

# Creating a blank algorithm to perform the analysis
treat.silent_create_algorithm(algorithm_name="VIPA spectrum analyser", 
                        version="v0", 
                        author="Pierre Bouvet", 
                        description="This algorithm allows the user to recover a frequency axis basing ourselves on a single Brillouin spectrum obtained with a VIPA spectrometer. Considering that only one Brillouin Stokes and anti-Stokes doublet is visible on the spectrum, the user can select the peaks he sees, and then perform a quadratic interpolation to obtain the frequency axis. This interpolation is obtained either by entering a value for the Brillouin shift of the material or by entering the value of the Free Spectral Range (FSR) of the spectrometer. The user can finally recenter the spectrum either using the average between a Stokes and an anti-Stokes peak or by choosing an elastic peak as zero frequency.")

# Adding points corresponding to the central peaks to the algorithm so as to normalize the PSD
for pt in x0:
    treat.add_point(position_center_window=pt, type_pnt="Other", window_width=2)
# treat.add_point(position_center_window=5, type_pnt="Stokes", window_width=2)
treat.normalize_data(threshold_noise = 0.05)

# Adding the peaks to fit
for pt, nat in zip(x0, nature):
    treat.add_point(position_center_window=pt, type_pnt=nat, window_width=2)

# Defining the model for fitting the peaks
treat.define_model(model="DHO", elastic_correction=False) 

# Estimating the linewidth from selected peaks
treat.estimate_width_inelastic_peaks(max_width_guess=5)

# Fitting all the selected inelastic peaks with multiple peaks fitting
bound_shift = [[pt-dx, pt+dx] for pt in x0]
bound_linewidth = [[0, linewidth_max] for _ in x0]
treat.single_fit_all_inelastic(guess_offset=True, 
                                update_point_position=True, 
                                bound_shift=bound_shift, 
                                bound_linewidth=bound_linewidth)


# Applying the algorithm to all the spectra (in the case where PSD is a 2D array)
treat.apply_algorithm_on_all()

treat.combine_results_FSR(FSR=200, keep_max_amplitude=False, amplitude_weight=False, shift_err_weight=False, position=None)

wrp.add_treated_data(path, name_group="Treated", treat = treat, overwrite=True)
wrp.add_abscissa(delay_axis, parent_group=f'{path}/Treated', name="Time around pulse (ms)", unit="ms", dim_start=0, dim_end=1, overwrite=True)

shift = treat.shift
shift_err = treat.shift_var**0.5
linewidth = treat.linewidth
linewidth_err = treat.linewidth_var**0.5
blt = treat.BLT
blt_err = treat.BLT_var**0.25


plt.figure()
plt.subplot(311)
plt.errorbar(delay_axis, shift, yerr=shift_err)
plt.xlabel("Delay from pulse (ms)")
plt.ylabel("Frequency shift (GHz)")
plt.subplot(312)
plt.errorbar(delay_axis, linewidth, yerr=linewidth_err)
plt.xlabel("Delay from pulse (ms)")
plt.ylabel("Linewidth (GHz)")
plt.subplot(313)
plt.errorbar(delay_axis, blt, yerr=blt_err)
plt.xlabel("Delay from pulse (ms)")
plt.ylabel("BLT")

plt.figure()
plt.plot(shift, linewidth)
plt.xlabel("Frequency shift (GHz)")
plt.ylabel("Linewidth (GHz)")

plt.show()
