import numpy as np
import math
import serial
import time

class TFPHandler:
    """Handles interaction with the TFP-1 device via serial communication."""
    
    BAUD_RATE = 57600
    RETRACE_MARKER = b'\xff'
    SCAN_STEP_QUANTUM = 0.25 # in ms
    SCAN_DURATION = 0.640 # in s

    def __init__(self, port=None):
        self.port = port
        self.serial_conn = None
        self._is_observing = False
        self.current_scan = []
        self.freq_axis_func = lambda nb_samples: np.arange(nb_samples)

    def validate_stimulation_range(self, value):
        """
        Ensures the value is a multiple of SCAN_STEP_QUANTUM.
        If not, rounds up to the nearest multiple.
        Returns (validated_value, was_updated).
        """
        if value <= 0:
            return 0.0, False
            
        # Check if it's already a multiple (using a small epsilon for float comparison)
        remainder = value % self.SCAN_STEP_QUANTUM
        if math.isclose(remainder, 0, abs_tol=1e-9) or math.isclose(remainder, self.SCAN_STEP_QUANTUM, abs_tol=1e-9):
            return value, False
            
        # Round up to the nearest multiple
        rounded_value = math.ceil(value / self.SCAN_STEP_QUANTUM) * self.SCAN_STEP_QUANTUM
        return rounded_value, True

    def connect(self, port=None):
        """Connect to the TFP device."""
        if port:
            self.port = port
        
        try:
            self.serial_conn = serial.Serial(self.port, self.BAUD_RATE, timeout=0.1)
            print(f"Connected to TFP on {self.port}")
            return True
        except Exception as e:
            print(f"Connection error to TFP on {self.port}: {e}")
            return False

    def disconnect(self):
        """Disconnect from the TFP device."""
        self._is_observing = False
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            print("Disconnected from TFP")
        self.serial_conn = None

    def decode_packet(self, b1, b2):
        """Decodes the 12-bit PMT counts and status bits."""
        # Byte 1: SH + U + 6 MSb of data
        # Byte 2: U + A + 6 LSb of data
        shutter = (b1 >> 7) & 0x01
        alignment = (b2 >> 6) & 0x01
        
        # Extract 6 bits from each byte and combine
        msb = b1 & 0x3F
        lsb = b2 & 0x3F
        counts = (msb << 6) | lsb
        return counts, shutter, alignment
    
    def frequency_axis(self, lmbda=None, mirror_spacing=None, scan_range=None):
        """Returns the frequency axis for the TFP."""
        if lmbda is None or mirror_spacing is None or scan_range is None:
            return
        c = 299792458
        FSR_Hz = c/(2*mirror_spacing*1e-3) # From TFP manual
        range_Hz = 2*scan_range / lmbda * FSR_Hz # From TFP manual
        self.freq_axis_func = lambda nb_samples: np.linspace(-range_Hz/2, range_Hz/2, nb_samples)

    def observe(self):
        """
        Continuously reads serial data and yields complete spectra.
        This is a generator that yields a list representing a full scan.
        """
        self._is_observing = True
        self.current_scan = []

        while self._is_observing:
            if not self.serial_conn or not self.serial_conn.is_open:
                lorentzian = lambda x, A, x0, sigma: A * (sigma**2 / ((x - x0)**2 + sigma**2))
                nu = np.linspace(-10, 10, 512)
                self.current_scan = lorentzian(nu, 1, -5, 1) + lorentzian(nu, 1, 5, 1) + np.random.rand(512) * 0.1
                yield self.current_scan
                time.sleep(0.4)
                continue
            
            else:
                if self.serial_conn.in_waiting > 0:
                    raw_byte = self.serial_conn.read(1)
                    
                    # Case: Retrace Phase (Scan finished)
                    if raw_byte == self.RETRACE_MARKER:
                        if self.current_scan:
                            yield self.current_scan
                            self.current_scan = []
                        continue
                    
                    # Case: Scan Phase (2-byte packets)
                    byte1 = ord(raw_byte)
                    byte2_raw = self.serial_conn.read(1)
                    if byte2_raw:
                        byte2 = ord(byte2_raw)
                        counts, shutter, align = self.decode_packet(byte1, byte2)
                        self.current_scan.append(counts)
                else:
                    # Small sleep to prevent busy waiting if no data
                    time.sleep(0.001)

    def stop_observation(self):
        """Signals the observe generator to stop."""
        self._is_observing = False

    def estimate_duration(self, channels, nb_samples, time_around_pulse_ms, nb_cycles):
        """Estimates the duration of the experiment and updates the remaining time label."""
        if len(channels) == 0:
            return 0
            
        elif len(channels) == 1:
            try:
                if nb_samples == 0:
                    return 0

                chan = channels[0]
                low, high = chan
                freq = self.freq_axis_func(nb_samples)

                idx0 = np.argmin(np.abs(freq - low))
                idx1 = np.argmin(np.abs(freq - high))
                
                nb_channels_scanned = abs(idx1 - idx0)
                # Each experiment consists in a virtual number of channels equal to the number of channel scanned plus the delay expressed in number of channels (one channel is scanned in 500 µs)
                N = nb_channels_scanned + (time_around_pulse_ms * 2)
                
                total_seconds = N * nb_cycles * self.SCAN_DURATION
                
                # Format as HH:MM:SS
                return total_seconds
            except Exception as e:
                print(f"Error estimating duration: {e}")
                return 0
        else:
            # We don't want to spam QMessageBox during interactivity
            print("Multi-window duration estimation not yet implemented.")
            return 0