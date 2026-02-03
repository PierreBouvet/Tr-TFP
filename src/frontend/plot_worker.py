from PyQt6.QtCore import QObject, pyqtSignal
import numpy as np

class PlotWorker(QObject):
    """Worker for processing 2D heatmap data in a background thread."""
    plot_ready = pyqtSignal(np.ndarray, np.ndarray, np.ndarray)

    def __init__(self):
        super().__init__()

    def process_data(self, chosen_results, delay_array, freq_axis_func, chosen_freq, time_around_pulse_ms):
        """
        Performs the heavy numpy slicing and mesh calculations.
        
        Args:
            results: Cumulative results array from ExperimentWorker.
            delay_array: Corresponding delay array.
            freq_axis_func: Function to generate frequency axis.
            chosen_freq: (low, high) tuple of selected frequency range.
            time_around_pulse_ms: Current time window setting.
        """
        if chosen_results is None or delay_array is None:
            return

        try:
            # 1. Get frequency axis
            freq = freq_axis_func(chosen_results.shape[1])

            # 2. Restrict to observed frequency window
            chosen_freq_idx = np.arange(np.argmin(np.abs(freq - chosen_freq[0])), np.argmin(np.abs(freq - chosen_freq[1]))+1)

            sub_freq = freq[chosen_freq_idx]
            chosen_results = chosen_results[:, chosen_freq_idx]
            chosen_delays = delay_array[:, chosen_freq_idx]

            # 4. Prepare Mesh Data
            # Add one last frequency/time value for PColorMesh vertices
            # PColorMesh with (N, M) data expects (N+1, M+1) vertices
            
            # Freq vertices
            freq_step = sub_freq[-1] - sub_freq[-2] if len(sub_freq) > 1 else 0
            freq_mesh = np.append(sub_freq, sub_freq[-1] + freq_step)
            
            # Prepare X (Frequency) and Y (Time Delay)
            X = np.tile(freq_mesh[np.newaxis, :], (chosen_results.shape[0] + 1, 1))
            Y = np.zeros((chosen_results.shape[0] + 1, chosen_results.shape[1] + 1))

            Y[:-1, :-1] = chosen_delays
            
            # Boundaries
            Y[-1, :-1] = Y[-2, :-1] + 0.5 
            Y[:, -1] = Y[:, -2] + (sub_freq[1] - sub_freq[0] if len(sub_freq) > 1 else 0) # Just a placeholder for the last column wall

            # Final check before emitting
            if X.shape != (chosen_results.shape[0] + 1, chosen_results.shape[1] + 1):
                return
            
            print(X[0, 0], X[-1, -1], Y[0, 0], Y[-1, -1], chosen_results.shape)

            self.plot_ready.emit(X, Y*1e-3, chosen_results)
            
        except Exception as e:
            print(f"PlotWorker error: {e}")
