from PyQt6.QtCore import QObject, pyqtSignal
import numpy as np
import time

class ExperimentWorker(QObject):
    progress_updated = pyqtSignal(int, str)
    finished = pyqtSignal()
    results_ready = pyqtSignal(np.ndarray, np.ndarray)
    results_updated = pyqtSignal(np.ndarray, np.ndarray)
    data_received = pyqtSignal(np.ndarray)
    error = pyqtSignal(str)

    def __init__(self, tfp_handler, ni_handler, delays, nb_cycles, pulse_length_ms, spectrum_len=1024):
        super().__init__()
        self.tfp_handler = tfp_handler
        self.ni_handler = ni_handler
        self.delays = delays
        self.nb_cycles = nb_cycles
        self.pulse_length_ms = pulse_length_ms
        self.spectrum_len = spectrum_len
        self._running = False
        self.results = None
        self.delay_array = None

    def run(self):
        self._running = True
        N = len(self.delays)
        self.results = np.zeros((N, self.spectrum_len))
        self.delay_array = np.zeros((N, self.spectrum_len))

        # Start the observation generator
        spectra_gen = self.tfp_handler.observe()
        
        try:
            for nbc in range(self.nb_cycles):
                for i, delay_ms in enumerate(self.delays):
                    if not self._running:
                        break

                    self.delay_array[i, :] = np.arange(self.spectrum_len) * 0.5 - delay_ms
                    # Update NI pulse delay (convert ms to seconds)
                    try:
                        self.ni_handler.stop_delayed_pulse()
                    except:
                        pass
                    self.ni_handler.start_delayed_pulse(delay = delay_ms / 1000.0, pulse_width=self.pulse_length_ms / 1000.0)
                    
                    # Capture and sum nb_cycles spectra
                
                    if not self._running:
                        break
                    try:
                        spectrum = next(spectra_gen)
                        # If spectrum is not complete, get the next one
                        if len(spectrum) != self.spectrum_len:
                            spectrum = next(spectra_gen)
                        
                        # Store summed spectra in results with the 'i' shift
                        self.results[i, :] += np.array(spectrum)
                        
                        # Emit the latest spectrum for real-time visualization
                        self.data_received.emit(np.array(spectrum))
                        
                        # Emit the cumulative results for the 2D map
                        self.results_updated.emit(self.results, self.delay_array)

                    except StopIteration:
                        self.error.emit("Observation generator stopped prematurely.")
                        return
                    
                    # Emit progress
                    progress = int(((i + nbc*N) / (N*self.nb_cycles)) * 100)
                    self.progress_updated.emit(progress, f"Cycle {nbc+1}/{self.nb_cycles} | Delay {i+1}/{N} ({delay_ms:.2f} ms)")
                
                if not self._running:
                    break
                
            if self._running:
                self.results_ready.emit(self.results, self.delay_array)
                
        except Exception as e:
            self.error.emit(str(e))
        finally:
            self._running = False
            self.tfp_handler.stop_observation()
            self.ni_handler.stop_delayed_pulse()
            self.finished.emit()

    def stop(self):
        self._running = False
        self.tfp_handler.stop_observation()
        self.ni_handler.stop_delayed_pulse()
