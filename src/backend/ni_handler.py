import numpy as np
import time

try:
    import nidaqmx
    import nidaqmx.constants as constants
    NIDAQ_AVAILABLE = True
except (ImportError, Exception):
    NIDAQ_AVAILABLE = False

from PyQt6.QtWidgets import QMessageBox

class NIHandler:
    """Handles interaction with the NI-USB-63401 device."""
    
    def __init__(self, device_name="cDAQ1", module_slot="Mod3", counter_path=None, source_terminal=None, output_terminal=None):
        self.device_name = device_name
        self.module_slot = module_slot
        
        # Use provided values or construct defaults
        self.counter_path = counter_path if counter_path else f"{device_name}/ctr0"
        self.source_terminal = source_terminal if source_terminal else f"/{device_name}{module_slot}/PFI0"
        self.output_terminal = output_terminal if output_terminal else f"/{device_name}{module_slot}/PFI4"
        
        self.is_mock = not NIDAQ_AVAILABLE
        self.task = None
        self.pulse_task = None
        
        if self.is_mock:
            print("NI-DAQmx not found. Operating in MOCK mode.")

    def connect(self):
        """Connect to the NI device and verify availability."""
        if self.is_mock:
            self._show_warning("NI-DAQmx driver not found. Switching to mock mode.")
            return True
            
        try:
            # Check if device exists by attempting to create a task
            with nidaqmx.Task() as test_task:
                # We don't do much here, just checking if we can even talk to the driver/device
                pass
            print(f"Connected to NI device: {self.device_name}")
            return True
        except Exception as e:
            self.is_mock = True
            self._show_warning(f"Failed to connect to NI device '{self.device_name}': {e}\nSwitching to mock mode.")
            return True

    def _show_warning(self, message):
        """Show a warning message box to the user."""
        QMessageBox.warning(
            None,
            "NI Connection Issue",
            message,
            QMessageBox.StandardButton.Ok
        )

    def list_modules(self):
        """List all available modules in the NI chassis."""
        if self.is_mock:
            return ["Mod1", "Mod2", "Mod3", "Mod4"]
        
        try:
            system = nidaqmx.system.System.local()
            modules = [dev.name for dev in system.devices]
            return modules
        except Exception as e:
            self._show_warning(f"Failed to list modules: {e}")
            return []
        
    def list_counters(self, module_name):
        """List all available counters in the NI module."""
        if self.is_mock:
            return [f"{module_name}/ctr0", f"{module_name}/ctr1", f"{module_name}/ctr2", f"{module_name}/ctr3"]
        
        try:
            system = nidaqmx.system.System.local()
            dev = system.devices[module_name]
            counters = [chan.name for chan in dev.co_physical_chans]
            return counters
        except Exception as e:
            self._show_warning(f"Failed to list counters: {e}")
            return []
        
    def list_pfi_terminals(self, module_name):
        """List all available PFI terminals in the NI module."""
        if self.is_mock:
            return [f"{module_name}/PFI0", f"{module_name}/PFI1", f"{module_name}/PFI2", f"{module_name}/PFI3", f"{module_name}/PFI4", f"{module_name}/PFI5", f"{module_name}/PFI6", f"{module_name}/PFI7"]
        
        try:
            system = nidaqmx.system.System.local()
            dev = system.devices[module_name]
            pfi_terminals = [term for term in dev.terminals if "PFI" in term]
            return pfi_terminals
        except Exception as e:
            self._show_warning(f"Failed to list PFI terminals: {e}")
            return []

    def start_delayed_pulse(self, delay, pulse_width=0.05):
        """
        Start a hardware-retriggerable delayed pulse.
        Based on working logic from test_ni_delay.py
        """
        if self.is_mock:
            print(f"[MOCK] Starting pulse: delay={delay}s, width={pulse_width}s")
            return

        try:
            # Stop any existing pulse task
            self.stop_delayed_pulse()

            self.pulse_task = nidaqmx.Task()
            
            # Configure the pulse generation
            self.pulse_task.co_channels.add_co_pulse_chan_time(
                counter=self.counter_path,
                units=constants.TimeUnits.SECONDS,
                idle_state=constants.Level.LOW,
                initial_delay=delay,
                low_time=0.001,
                high_time=pulse_width
            )
            self.pulse_task.co_channels[0].co_pulse_term = self.output_terminal
            
            # Configure for hardware retriggering
            self.pulse_task.triggers.start_trigger.cfg_dig_edge_start_trig(
                trigger_source = self.source_terminal, 
                trigger_edge = constants.Edge.RISING)
            self.pulse_task.triggers.start_trigger.retriggerable = True
            
            self.pulse_task.start()

        except Exception as e:
            print(f"Failed to start NI pulse: {e}")
            self._show_warning(f"Failed to start NI pulse: {e}")

    def stop_delayed_pulse(self):
        """Stop and close the delayed pulse task."""
        if self.is_mock:
            print("[MOCK] Stopping pulse")
            return

        if self.pulse_task:
            try:
                self.pulse_task.stop()
                self.pulse_task.close()
            except Exception as e:
                print(f"Error stopping pulse task: {e}")
            finally:
                self.pulse_task = None

    def _mock_measure_period(self, samples_to_collect):
        """Generate mock period data for testing without hardware."""
        print(f"Generating {samples_to_collect} mock samples...")
        # Simulate some jitter around 0.1 seconds (10Hz)
        base_period = 0.1
        jitter = np.random.normal(0, 0.001, samples_to_collect)
        return base_period + jitter

    def disconnect(self):
        """Cleanup NI resources."""
        if not self.is_mock:
            print(f"Disconnecting from {self.device_name}...")
        pass
