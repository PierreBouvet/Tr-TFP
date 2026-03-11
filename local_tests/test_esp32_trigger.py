import sys
import os
import time
import numpy as np

# Add src to path to import backend modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from backend.esp32_handler import ESP32Handler
import serial.tools.list_ports

def get_esp32_port():
    ports = list(serial.tools.list_ports.comports())
    if not ports:
        print("No serial ports found!")
        return None
        
    print("Available ports:")
    for i, p in enumerate(ports):
        print(f"{i}: {p.device} - {p.description}")
        
    idx = input("Select port index for ESP32 (default 0): ")
    if not idx:
        idx = 0
    else:
        idx = int(idx)
        
    return ports[idx].device

def main():
    print("=== ESP32 Trigger System Test ===")
    
    port = get_esp32_port()
    if not port:
        return

    handler = ESP32Handler(port=port)
    
    if not handler.connect():
        print("Exiting...")
        return

    try:
        # Generate test sequence
        # Linear Ramp: 1ms, 2ms, ... 10ms
        delays_ms = np.linspace(1.0, 10.0, 10)
        print(f"\nGenerated Test Pattern: {delays_ms} ms")
        
        # Configure
        handler.configure_delays(delays_ms)
        
        input("\nPress ENTER to START triggering... (Make sure OScope is connected per schematic)")
        
        print("\n--- SCHEMATIC REMINDER ---")
        print("GPIO 16 (RX2) -> INPUT TRIGGER (Function Generator)")
        print("GPIO 17 (TX2) -> OUTPUT TRIGGER (Scope Ch2)")
        print("--------------------------\n")
        
        response = handler.start_triggering()
        print(f"Start Response: {response}")
        
        print("\nSystem is RUNNING.")
        print("Expected Behavior:")
        print("On each Input Trigger rising edge, Output Trigger should pulse after:")
        for i, d in enumerate(delays_ms):
            print(f"Trigger #{i+1}: Delay = {d:.2f} ms")
        print("(Sequence repeats)")
        
        input("\nPress ENTER to STOP and EXIT...")
        
        handler.stop_triggering()
        
    except KeyboardInterrupt:
        print("\nInterrupted.")
    finally:
        handler.disconnect()
        print("Done.")

if __name__ == "__main__":
    main()
