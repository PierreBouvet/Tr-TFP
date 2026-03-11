# ESP32 Trigger System

## Connections

| Pin Name | GPIO | Function | Description |
|---|---|---|---|
| **D16 (RX2)** | 16 | **Trigger INPUT** | Connect to TFP Output or Master Clock. Signals the start of a cycle. |
| **D17 (TX2)** | 17 | **Trigger OUTPUT** | Connect to Impulse Trigger Input. This signal is delayed relative to Input. |
| **GND** | GND | **Ground** | Common Ground with both Input and Output devices. |
| **USB** | - | **Control** | Connect to Computer for configuration and power. |

## ASCII Schematic
```
      +---------------------+
      |        ESP32        |
      |                     |
TFP   +---> GPIO 16 (IN)    |
      |                     |
Pulse <---+ GPIO 17 (OUT)   |
      |                     |
GND   +---- GND             |
      |                     |
PC    <===> USB             |
      +---------------------+
```

## Protocol (Serial 115200 baud)

1.  **Stop**: `STOP\n`
2.  **Reset**: `RESET\n`
3.  **Configure**: `CONFIG <N>\n` where N is number of pulses in the sequence.
4.  **Load Data**: `DATA <index> <delay_micros>\n` for each index 0 to N-1.
5.  **Start**: `START\n`

The ESP32 will wait for a rising edge on GPIO 16.
Once received, it waits for `delay_list[current_index]` microseconds.
Then it pulses GPIO 17 HIGH for 10 microseconds.
It increments `current_index` (modulo N).
