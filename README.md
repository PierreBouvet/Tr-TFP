# Tr-TFP

Tr-TFP is a software suite designed to interface a computer with a Tandem Fabry-Perot (TFP) interferometer and a National Instruments (NI) USB-6341 data acquisition card. It enables synchronized signal generation and high-speed data acquisition for Brillouin Light Scattering (BLS) experiments.

## Features

- **TFP Interface**: Configuration and control of scanning parameters.
- **NI Integration**: Precise timing of pulse triggers with respect to scanning of TFP with NI modules.
- **Real-time Visualization**: Live feedback of acquired Brillouin spectra.
- **Time-Resolved Measurements**: Support for experiment protocols with timing delays.

## Installation

### Prerequisites

> [!IMPORTANT]  
> The NI-DAQmx drivers only work on Windows and Linux. For macOS, the drivers are not available, so the NI card cannot be used.

- Python 3.8+
- [NI-DAQmx drivers](https://www.ni.com/en-us/support/downloads/drivers/download.ni-daqmx.html) (required for hardware communication)

### Setup

1. Clone the repository.
2. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On macOS/Linux
   # or
   .venv\Scripts\activate     # On Windows
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the main application:
```bash
python src/main.py
```

## Documentation

Full documentation is available in the `docs/` directory.

### Building Documentation

To build the HTML documentation, you need Sphinx:
```bash
pip install -r docs/requirements.txt
cd docs
make html
```
The generated documentation will be located in `docs/build/html/index.html`.

## Project Structure

- `src/`: Core logic and GUI implementation.
  - `backend/`: Hardware handlers for TFP and NI devices.
  - `frontend/`: PyQt-based user interface components.
- `docs/`: Sphinx documentation source and build files.
- `images/`: SVG diagrams used in documentation.
- `local_tests/`: Helper scripts and test data.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

&copy; 2026 Pierre Bouvet
