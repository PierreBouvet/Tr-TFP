import serial
import time
import numpy as np

class ESP32Handler:
    """
    Handles communication with the ESP32 Trigger System.
    """
    
    BAUD_RATE = 115200
    
    def __init__(self, port=None):
        self.port = port
        self.serial_conn = None
        
    def connect(self):
        """Connect to the ESP32 serial port."""
        if not self.port:
            raise ValueError("Serial port not specified.")
            
        try:
            self.serial_conn = serial.Serial(self.port, self.BAUD_RATE, timeout=0.1)
            time.sleep(2) # Wait for ESP32 reset
            print(f"Connected to ESP32 on {self.port}")
            self.stop_triggering() # Ensure clean state
            return True
        except Exception as e:
            print(f"Failed to connect to ESP32 on {self.port}: {e}")
            return False
            
    def disconnect(self):
        """Close the serial connection."""
        if self.serial_conn and self.serial_conn.is_open:
            self.stop_triggering()
            self.serial_conn.close()
            print("Disconnected from ESP32")
            
    def _send_command(self, cmd):
        """Send a command string and wait for acknowledgement."""
        if not self.serial_conn:
            return None
        
        self.serial_conn.write(f"{cmd}\n".encode())
        time.sleep(0.005) # Small buffer
        response = self.serial_conn.readline().decode().strip()
        return response

    def configure_delays(self, delays_ms):
        """
        Uploads a list of delays (in milliseconds) to the ESP32.
        """
        delays_us = (np.array(delays_ms) * 1000).astype(int)
        num_delays = len(delays_us)
        
        print(f"Configuring {num_delays} delays...")
        
        # 1. Reset/Config
        resp = self._send_command(f"CONFIG {num_delays}")
        if not resp or "OK" not in resp:
            print(f"Error configuring ESP32: {resp}")
            return False
            
        # 2. specific data upload
        # Doing this one by one might be slow for large N, but reliable.
        # We can optimize to batch if needed later.
        for i, d in enumerate(delays_us):
            self._send_command(f"DATA {i} {d}")
            # Optional: check response for flow control if N is large
            
        print("Delay configuration complete.")
        return True

    def start_triggering(self):
        """Starts the trigger loop on the ESP32."""
        print("Starting triggering...")
        return self._send_command("START")
        
    def stop_triggering(self):
        """Stops the trigger loop."""
        print("Stopping triggering...")
        return self._send_command("STOP")
