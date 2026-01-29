
import sys
import os

# Add src to path
sys.path.append(os.path.abspath("src"))

from backend.ni_handler import NIHandler

def test_ni_handler_custom_init():
    print("Testing NIHandler custom initialization...")
    handler = NIHandler(
        device_name="MyDevice",
        counter_path="MyDevice/ctr1",
        source_terminal="/MyDevice/PFI2",
        output_terminal="/MyDevice/PFI5"
    )
    
    assert handler.device_name == "MyDevice"
    assert handler.counter_path == "MyDevice/ctr1"
    assert handler.source_terminal == "/MyDevice/PFI2"
    assert handler.output_terminal == "/MyDevice/PFI5"
    print("NIHandler custom initialization test PASSED.")

def test_ni_handler_default_init():
    print("Testing NIHandler default initialization...")
    handler = NIHandler(device_name="Dev1", module_slot="Mod1")
    
    assert handler.device_name == "Dev1"
    assert handler.counter_path == "Dev1/ctr0"
    assert handler.source_terminal == "/Dev1Mod1/PFI0"
    assert handler.output_terminal == "/Dev1Mod1/PFI4"
    print("NIHandler default initialization test PASSED.")

if __name__ == "__main__":
    try:
        test_ni_handler_custom_init()
        test_ni_handler_default_init()
        print("\nAll unit tests PASSED.")
    except AssertionError as e:
        print(f"\nUnit test FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        sys.exit(1)
