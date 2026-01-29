import nidaqmx
import time
from nidaqmx.constants import Edge, TimeUnits, Level
import numpy as np

# Configuration
CHASSIS = "cDAQ1"
MODULE_SLOT = "Mod3"
CTR_CHAN = f"{CHASSIS}/ctr0"
TRIG_IN = f"/{CHASSIS}{MODULE_SLOT}/PFI0"  # second input trigger pin identical to PFI0
TRIG_OUT = f"/{CHASSIS}{MODULE_SLOT}/PFI4"

def run_dynamic_task(delay_val, pulse_width_val=0.05):
    task = nidaqmx.Task()
    # Configure the pulse generation
    task.co_channels.add_co_pulse_chan_time(
        counter=CTR_CHAN,
        units=TimeUnits.SECONDS,
        idle_state=Level.LOW,
        initial_delay=delay_val,
        low_time=0.01,
        high_time=pulse_width_val
    )
    task.co_channels[0].co_pulse_term = TRIG_OUT
    
    # Configure for hardware retriggering
    task.triggers.start_trigger.cfg_dig_edge_start_trig(
        trigger_source = TRIG_IN, 
        trigger_edge = Edge.RISING)
    task.triggers.start_trigger.retriggerable = True
    
    task.start()
    return task

delay = np.arange(10)*0.05
for dl in delay:
    task = run_dynamic_task(delay_val = dl, pulse_width_val = 0.05)
    time.sleep(1)
    task.stop()
    task.close()
input("Press Enter to stop...")
