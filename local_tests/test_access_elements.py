import nidaqmx
from nidaqmx.system import System

system = System.local()
CHASSIS_NAME = "cDAQ1"

# Get all devices (modules) that belong to the specified chassis
modules = [dev.name for dev in system.devices]

print(f"Modules in {CHASSIS_NAME}: {modules}")

module_name = "cDAQ1Mod3" # Example module name
dev = system.devices[module_name]

# List counter input and output physical channels
counters = [chan.name for chan in dev.co_physical_chans]
print(f"Counters available for {module_name}: {counters}")

# List all PFI terminals for the module
pfi_terminals = [term for term in dev.terminals if "PFI" in term]

print(f"PFI Terminals on {module_name}:")
for pfi in pfi_terminals:
    print(f" - {pfi}")
