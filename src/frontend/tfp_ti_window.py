import sys
import numpy as np
import pyqtgraph as pg
from PyQt6.QtWidgets import (
    QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLabel, 
    QGroupBox, QLineEdit, QFormLayout, QSpinBox, QMessageBox, QFileDialog
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont

from backend.tfp_handler import TFPHandler
from frontend.tfp_worker import TFPWorker
from frontend.connection_dialog import ConnectionDialog

class CollapsibleSection(QWidget):
    toggled = pyqtSignal(bool)

    def __init__(self, title="", parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        self.toggle_button = QPushButton(title)
        self.toggle_button.setCheckable(True)
        self.toggle_button.setChecked(False)
        self.toggle_button.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 10px;
                background-color: #3d3d3d;
                border: none;
                border-bottom: 1px solid #2d2d2d;
                font-weight: bold;
                color: #e1e1e1;
            }
            QPushButton:checked {
                background-color: #505050;
                border-bottom: 2px solid #007acc;
            }
        """)

        self.content_area = QWidget()
        self.content_layout = QVBoxLayout(self.content_area)
        self.content_area.setVisible(False)

        self.layout.addWidget(self.toggle_button)
        self.layout.addWidget(self.content_area)

        self.toggle_button.clicked.connect(self.on_toggle)

    def on_toggle(self):
        checked = self.toggle_button.isChecked()
        self.content_area.setVisible(checked)
        self.toggled.emit(checked)

    def set_expanded(self, expanded):
        self.toggle_button.setChecked(expanded)
        self.content_area.setVisible(expanded)

class TFP_TIWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Time-Invariant TFP Interface")
        self.setMinimumSize(800, 600)
        self.setStyleSheet("""
            QMainWindow { background-color: #1e1e1e; }
            QGroupBox {
                border: 2px solid #3d3d3d;
                border-radius: 8px;
                margin-top: 1ex;
                padding: 10px;
                background-color: #252526;
                color: #e1e1e1;
                font-weight: bold;
            }
            QLabel { color: #e1e1e1; }
            QPushButton {
                background-color: #3d3d3d;
                color: #e1e1e1;
                border-radius: 4px;
                padding: 8px;
            }
            QPushButton:hover { background-color: #505050; }
            QLineEdit, QSpinBox {
                background-color: #3d3d3d;
                color: #e1e1e1;
                border: 1px solid #555;
                padding: 4px;
            }
        """)
        
        # Central Widget & Layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        
        # Initialize Logic
        self.tfp_handler = TFPHandler()
        self.observation_thread = None
        self.observation_worker = None
        self.nb_samples = 0
        self.sections = []

        # -- UI Building --
        self.setup_top_panel()
        self.setup_bottom_panel()
        self.setup_navigation_panel()

    def setup_top_panel(self):
        """Top Panel: Graph + Observation Controls"""
        self.top_panel = QGroupBox("Signal Observation")
        layout = QVBoxLayout(self.top_panel)
        
        # Plot
        self.plot_widget = pg.PlotWidget(title="Counts vs Frequency shift")
        self.plot_widget.setBackground('#1e1e1e')
        self.plot_widget.setLabel('left', 'Counts', units='')
        self.plot_widget.setLabel('bottom', 'Frequency shift', units='Hz')
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.curve = self.plot_widget.plot(pen=pg.mkPen(color='#007acc', width=2))
        layout.addWidget(self.plot_widget)
        
        # Buttons
        btn_layout = QHBoxLayout()
        self.observe_btn = QPushButton("Observe")
        self.stop_observe_btn = QPushButton("Stop observing")
        self.stop_observe_btn.setEnabled(False)
        
        self.observe_btn.clicked.connect(self.start_observation)
        self.stop_observe_btn.clicked.connect(self.stop_observation)
        
        btn_layout.addWidget(self.observe_btn)
        btn_layout.addWidget(self.stop_observe_btn)
        layout.addLayout(btn_layout)
        
        # CONNECT BUTTON
        self.connect_btn = QPushButton("Connect TFP")
        self.connect_btn.clicked.connect(self.connect_device)
        self.connect_btn.setStyleSheet("background-color: #2d5a27;")
        btn_layout.addWidget(self.connect_btn)
        
        self.main_layout.addWidget(self.top_panel, 60) # 60% stretch

    def setup_bottom_panel(self):
        """Bottom Panel: Collapsible Options"""
        self.bottom_panel = QWidget()
        layout = QVBoxLayout(self.bottom_panel)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # 1. TFP Frequency Section
        self.freq_section = CollapsibleSection("TFP channel frequency")
        freq_form = QFormLayout()
        
        self.wavelength = QLineEdit()
        self.wavelength.setPlaceholderText("nm")
        self.wavelength.editingFinished.connect(self.update_frequency_axis)
        
        self.mirror_spacing = QLineEdit()
        self.mirror_spacing.setPlaceholderText("mm")
        self.mirror_spacing.editingFinished.connect(self.update_frequency_axis)
        
        self.scanning_range = QLineEdit()
        self.scanning_range.setPlaceholderText("µm (piezo)")
        self.scanning_range.editingFinished.connect(self.update_frequency_axis)

        freq_form.addRow("Wavelength (nm):", self.wavelength)
        freq_form.addRow("Mirror spacing (mm):", self.mirror_spacing)
        freq_form.addRow("Scanning range (nm):", self.scanning_range)
        self.freq_section.content_layout.addLayout(freq_form)
        self.sections.append(self.freq_section)
        layout.addWidget(self.freq_section)
        
        # 2. Automated Measure Section
        self.measure_section = CollapsibleSection("Automated measure")
        measure_layout = QVBoxLayout()
        
        form = QFormLayout()
        self.cycles_spin = QSpinBox()
        self.cycles_spin.setRange(1, 10000)
        self.cycles_spin.setValue(10)
        form.addRow("Number of cycles:", self.cycles_spin)
        measure_layout.addLayout(form)
        
        self.start_measure_btn = QPushButton("Start Measure")
        self.start_measure_btn.setStyleSheet("background-color: #2d5a27; font-size: 14px; padding: 10px;")
        self.start_measure_btn.clicked.connect(self.run_automated_measure)
        measure_layout.addWidget(self.start_measure_btn)
        
        self.measure_section.content_layout.addLayout(measure_layout)
        self.sections.append(self.measure_section)
        layout.addWidget(self.measure_section)
        
        # Mutual Exclusivity
        for section in self.sections:
            section.toggled.connect(self.on_section_toggled)

        self.main_layout.addWidget(self.bottom_panel, 40) # 40% stretch

    def setup_navigation_panel(self):
        nav_layout = QHBoxLayout()
        back_btn = QPushButton("Back to Menu")
        back_btn.clicked.connect(self.go_back)
        nav_layout.addWidget(back_btn)
        
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet("background-color: #7a2d2d;")
        close_btn.clicked.connect(self.close)
        nav_layout.addWidget(close_btn)
        
        self.main_layout.addLayout(nav_layout)

    # --- Logic ---

    def on_section_toggled(self, checked):
        if not checked: return
        sender = self.sender()
        for section in self.sections:
            if section != sender:
                section.set_expanded(False)

    def connect_device(self):
        dialog = ConnectionDialog(self, show_ni=False)
        if dialog.exec():
            selection = dialog.get_selection()
            port = selection['tfp_port']
            if self.tfp_handler.connect(port):
                QMessageBox.information(self, "Success", f"Connected to TFP on {port}")
                self.connect_btn.setText("Connected")
                self.connect_btn.setEnabled(False)

    def start_observation(self):
        self.observe_btn.setEnabled(False)
        self.stop_observe_btn.setEnabled(True)
        
        self.observation_thread = QThread()
        self.observation_worker = TFPWorker(self.tfp_handler)
        self.observation_worker.moveToThread(self.observation_thread)
        
        self.observation_thread.started.connect(self.observation_worker.run)
        self.observation_worker.data_received.connect(self.update_plot)
        self.observation_worker.finished.connect(self.observation_thread.quit)
        self.observation_worker.finished.connect(self.observation_worker.deleteLater)
        self.observation_thread.finished.connect(self.observation_thread.deleteLater)
        
        self.observation_thread.start()

    def stop_observation(self):
        if self.observation_worker:
            self.observation_worker.stop()
        self.observe_btn.setEnabled(True)
        self.stop_observe_btn.setEnabled(False)

    def update_plot(self, data):
        self.nb_samples = len(data)
        x_axis = self.tfp_handler.freq_axis_func(self.nb_samples)
        self.curve.setData(x_axis, data)

    def update_frequency_axis(self):
        try:
            lmbda = float(self.wavelength.text()) if self.wavelength.text() else None
            spacing = float(self.mirror_spacing.text()) if self.mirror_spacing.text() else None
            scan_range = float(self.scanning_range.text()) if self.scanning_range.text() else None
            
            self.tfp_handler.frequency_axis(lmbda, spacing, scan_range)
        except ValueError:
            pass

    def run_automated_measure(self):
        # 1. Stop observation if running
        if self.observe_btn.isEnabled() == False:
            self.stop_observation()
            # Wait a bit? Or simple flag check
        
        # 2. Get Filename
        from frontend.hdf5_save_dialog import HDF5SaveDialog
        dialog = HDF5SaveDialog(self)
        if not dialog.exec(): return
        
        selection = dialog.get_selection()
        filepath = selection["file_path"]
        group = selection["selected_group"]
        
        # 3. Perform Acquisition (Blocking for now, or thread?)
        # For simplicity in this new window, let's do a blocking loop with progress dialog,
        # OR reuse a simplified worker. Let's do a simple loop here for first iteration.
        
        nb_cycles = self.cycles_spin.value()
        
        self.start_measure_btn.setEnabled(False)
        self.start_measure_btn.setText("Measuring...")
        
        try:
            # We need to manually drive the handler's generator
            spectra_gen = self.tfp_handler.observe()
            accumulated = None
            
            for i in range(nb_cycles):
                spectrum = next(spectra_gen)
                if accumulated is None:
                    accumulated = np.array(spectrum, dtype=float)
                else:
                    if len(spectrum) == len(accumulated):
                        accumulated += spectrum
                
                # Process events to keep UI responsive
                QMessageBox.information(self, "Info", f"Cycle {i+1}/{nb_cycles}") if i % 10 == 0 else None 
                # ^ That's annoying. Let's just print or update label
                self.start_measure_btn.setText(f"Measuring... {i+1}/{nb_cycles}")
                sys.stdout.flush()
                
            self.tfp_handler.stop_observation()
            
            # Save
            self.save_data(filepath, group, accumulated)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
        finally:
            self.start_measure_btn.setEnabled(True)
            self.start_measure_btn.setText("Start Measure")

    def save_data(self, filepath, group_name, data):
        try:
            from HDF5_BLS import Wrapper
            wrp = Wrapper(filepath)
            
            freq = self.tfp_handler.freq_axis_func(len(data))
            
            # Create sub-group for this specific run? Or just datasets?
            # Let's save as 'Spectrum_N'
            # Check existing to increment? The Dialog handles selection. Let's assume user picked a target.
            
            # Reshape data to 2D (1 x N_freq) for add_PSD compatibility
            psd_data = np.atleast_2d(data)
            
            wrp.add_frequency(freq*1e-9, group_name, name="Frequency") # GHz
            
            # Add a dummy delay of 0 since this is time-invariant
            wrp.add_abscissa(np.array([0.0]), group_name, name="Delays")
            
            wrp.add_PSD(psd_data, group_name, name="PSD")
            
            # Attributes
            attrs = {
                "Cycles": self.cycles_spin.value(),
                "Type": "Time-Invariant"
            }
            wrp.add_attributes(attrs, parent_group=group_name)
            wrp.close()
            
            QMessageBox.information(self, "Saved", f"Data saved to {filepath}")
            
        except Exception as e:
             QMessageBox.critical(self, "Save Error", str(e))

    def go_back(self):
        from frontend.spectrometer_window import SpectrometerWindow
        self.menu = SpectrometerWindow()
        self.menu.show()
        self.close()

    def closeEvent(self, event):
        self.stop_observation()
        if self.tfp_handler:
            self.tfp_handler.disconnect()
        event.accept()
