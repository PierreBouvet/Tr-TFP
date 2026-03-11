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

group = 'Brillouin/Stimulation'

print(wrp.get_children_elements(group))

# # elt = '/Brillouin/Stimulation/100V 50ms between electrode green part'
path1 = 'Brillouin/Control/260223/01'
path2 = 'Brillouin/Stimulation/260223/root stimulation 100ms 100V'

delay1 = wrp[f'{path1}/Treated/Time around pulse (ms)']
delay2 = wrp[f'{path2}/Treated/Time around pulse (ms)']

shift1 = wrp[f'{path1}/Treated/Shift']
linewidth1 = wrp[f'{path1}/Treated/Linewidth']
shift2 = wrp[f'{path2}/Treated/Shift']
linewidth2 = wrp[f'{path2}/Treated/Linewidth']

plt.figure()
plt.subplot(211)
plt.plot(delay1, shift1, label = "No stimulation")
plt.plot(delay2, shift2, label = "100V 100ms @5 min")
plt.xlabel("Time (min)")
plt.ylabel("Frequency shift (GHz)")
plt.legend()
plt.subplot(212)
plt.plot(delay1, linewidth1)
plt.plot(delay2, linewidth2)
plt.xlabel("Time (min)")
plt.ylabel("Linewidth (GHz)")
plt.show()