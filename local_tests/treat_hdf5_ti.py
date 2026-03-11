from HDF5_BLS import Wrapper
import matplotlib.pyplot as plt 
import numpy as np
from HDF5_BLS_treat import Treat
import time

import os


main_dic = '/Volumes/LAUDATE/Data/260216 - Plants'

# for d in os.listdir(main_dic):
#     print(d)

filepath = f'{main_dic}/All Measures.h5'

wrp = Wrapper(filepath)

# for g in wrp.get_children_elements('Brillouin'):
#     print(g)

group = 'Brillouin/Australis'

# print(wrp.get_children_elements(group))

path = 'Brillouin/Australis/Control/260224 - 01'
# path = 'Brillouin/Australis/Stimulated/260224 - 01'

# print(wrp.get_children_elements(path))

attributes = wrp.get_attributes(path)

delays = wrp[path + '/Delays']
freq = wrp[path + '/Frequency']
psd = wrp[path + '/PSD']

# m = 8000

# delays = delays[:m]
# psd = psd[:m]

# Average every N_avg consecutive lines
N_avg = 2**3
new_psd = np.mean(psd.reshape(-1, N_avg, psd.shape[1]), axis=1)
new_delays = np.mean(delays.reshape(-1, N_avg), axis=1)
# User likely meant new_delays if asking for new arrays of averaged values
# But let's define new_freq as freq (unchanged) just in case
new_freq = freq 

# Use the new averaged data
psd = new_psd
delays = new_delays
freq = new_freq

delays = delays//60 + delays%60/60


plt.imshow(psd, aspect='auto', origin='lower', vmin = 0, vmax = 3e2, extent=[freq[0], freq[-1], delays[-1], delays[0]], cmap = 'turbo')
plt.xlabel("Frequency shift(GHz)")
plt.ylabel("Time (min)")

x0 = [-7, 7.8]
nature = ['Anti-Stokes', 'Stokes']
dx = 5
linewidth_max = 2.5
bound_shift = [[-7.2, -6.6], [7.6, 7.9]]

# Initialising the Treat object on the a doublet of frequency and PSD
treat = Treat(frequency = freq, PSD = psd)

# # Function to display progress
def display_progress(current, total):
    print(f"\rProcessing spectrum {current}/{total} ({current/total*100:.1f}%)", end="", flush=True)

treat._progress_callback = display_progress 

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
treat.define_model(model="DHO", elastic_correction=True) 

# Estimating the linewidth from selected peaks
treat.estimate_width_inelastic_peaks(max_width_guess=5)

# Fitting all the selected inelastic peaks with multiple peaks fitting

bound_linewidth = [[0, linewidth_max] for _ in x0]
treat.single_fit_all_inelastic(guess_offset=True, 
                                update_point_position=True, 
                                bound_shift=bound_shift, 
                                bound_linewidth=bound_linewidth)


# Applying the algorithm to all the spectra (in the case where PSD is a 2D array)
strt = time.time()
treat.apply_algorithm_on_all()
end = time.time()
print(f"Time taken: {end-strt}")
shift = treat.shift
shift_err = treat.shift_var**0.5
linewidth = treat.linewidth
linewidth_err = treat.linewidth_var**0.5
blt = treat.BLT
blt_err = treat.BLT_var**0.25


treat.combine_results_FSR(FSR=200, keep_max_amplitude=False, amplitude_weight=False, shift_err_weight=False, position=None)

wrp.add_treated_data(path, name_group="Treated", treat = treat, overwrite=True)
wrp.add_abscissa(delays, parent_group=f'{path}/Treated', name="Time around pulse (ms)", unit="ms", dim_start=0, dim_end=1, overwrite=True)

shift = treat.shift
shift_err = treat.shift_var**0.5
linewidth = treat.linewidth
linewidth_err = treat.linewidth_var**0.5
blt = treat.BLT
blt_err = treat.BLT_var**0.5

plt.figure()
plt.subplot(311)
# plt.errorbar(delays, shift, yerr=shift_err)
plt.plot(delays, shift)
plt.xlabel("Time (min)")
plt.ylabel("Frequency shift (GHz)")
plt.subplot(312)
# plt.errorbar(delays, linewidth, yerr=linewidth_err)
plt.plot(delays, linewidth)
plt.xlabel("Time (min)")
plt.ylabel("Linewidth (GHz)")
plt.subplot(313)
# plt.errorbar(delays, blt, yerr=blt_err)
plt.plot(delays, blt)
plt.xlabel("Time (min)")
plt.ylabel("BLT")

plt.figure()
plt.plot(shift, linewidth)
plt.xlabel("Frequency shift (GHz)")
plt.ylabel("Linewidth (GHz)")


plt.show()



