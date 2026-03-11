import sys
import numpy as np
from PyQt6.QtWidgets import (
    QMainWindow, QVBoxLayout, QHBoxLayout, QGridLayout, QWidget, 
    QPushButton, QLabel, QFrame, QLineEdit, QComboBox, QFormLayout, 
    QProgressBar, QGroupBox, QMessageBox, QSpinBox, QDoubleSpinBox
)
import time
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QFont
import pyqtgraph as pg

from frontend.connection_dialog import ConnectionDialog
from backend.tfp_handler import TFPHandler
from backend.ni_handler import NIHandler
from frontend.tfp_worker import TFPWorker

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

class TFP_DLSWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TFP and DLS Analysis")
        self.setMinimumSize(1000, 800)
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
                min-width: 80px;
            }
            QPushButton:hover { background-color: #505050; }
            QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
                background-color: #3d3d3d;
                color: #e1e1e1;
                border: 1px solid #555;
                padding: 4px;
            }
            QProgressBar {
                border: 1px solid #555;
                border-radius: 4px;
                text-align: center;
                background-color: #3d3d3d;
                color: white;
            }
            QProgressBar::chunk { background-color: #007acc; }
        """)

        # Central widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QGridLayout(self.central_widget)
        self.main_layout.setSpacing(15)

        # Handlers
        self.tfp_handler = TFPHandler()
        self.ni_handler = NIHandler()

        # Threads/Workers
        self.observation_thread = None
        self.observation_worker = None

        # --- Top Left: TFP Panel ---
        self.setup_tfp_panel()

        # --- Top Right: DLS Panel ---
        self.setup_dls_panel()

        # --- Bottom Left: Parameters Panel ---
        self.setup_parameters_panel()

        # --- Bottom Right: Control Panel ---
        self.setup_control_panel()

        # Bottom Buttons
        bottom_buttons = QHBoxLayout()
        self.back_btn = QPushButton("Back to Spectrometer choice")
        self.back_btn.clicked.connect(self.on_back_clicked)
        self.close_btn = QPushButton("Close Application")
        self.close_btn.setStyleSheet("background-color: #7a2d2d;")
        self.close_btn.clicked.connect(self.close)
        bottom_buttons.addWidget(self.back_btn)
        bottom_buttons.addStretch()
        bottom_buttons.addWidget(self.close_btn)
        self.main_layout.addLayout(bottom_buttons, 2, 0, 1, 2)

    def setup_tfp_panel(self):
        panel = QGroupBox("TFP Signal Observation")
        layout = QVBoxLayout(panel)
        self.tfp_plot = pg.PlotWidget(title="Counts vs Frequency shift")
        self.tfp_plot.setBackground('#1e1e1e')
        self.tfp_curve = self.tfp_plot.plot(pen=pg.mkPen(color='#007acc', width=1))
        layout.addWidget(self.tfp_plot)
        
        btn_layout = QHBoxLayout()
        self.observe_btn = QPushButton("Observe")
        self.stop_observe_btn = QPushButton("Stop observing")
        self.stop_observe_btn.setEnabled(False)
        self.observe_btn.clicked.connect(self.on_observe_clicked)
        self.stop_observe_btn.clicked.connect(self.on_stop_observing_clicked)
        btn_layout.addWidget(self.observe_btn)
        btn_layout.addWidget(self.stop_observe_btn)
        layout.addLayout(btn_layout)
        
        self.main_layout.addWidget(panel, 0, 0)

    def setup_dls_panel(self):
        panel = QGroupBox("Dynamic Light Scattering Analysis")
        layout = QVBoxLayout(panel)
        self.dls_plot = pg.PlotWidget(title="DLS Analysis (Autocorrelation)")
        self.dls_plot.setBackground('#1e1e1e')
        self.dls_curve = self.dls_plot.plot(pen=pg.mkPen(color='#ffaa00', width=1))
        layout.addWidget(self.dls_plot)
        self.main_layout.addWidget(panel, 0, 1)

    def setup_parameters_panel(self):
        panel = QGroupBox("Parameters")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(5, 15, 5, 5)
        
        self.sections = []

        # TFP Parameters
        self.tfp_section = CollapsibleSection("TFP Parameters")
        tfp_form = QFormLayout()
        self.nb_channels_cb = QComboBox()
        self.nb_channels_cb.addItems(["256", "512", "1024"])
        self.nb_channels_cb.setCurrentText("512")
        tfp_form.addRow("Number of channels:", self.nb_channels_cb)
        self.tfp_section.content_layout.addLayout(tfp_form)
        layout.addWidget(self.tfp_section)
        self.sections.append(self.tfp_section)

        # DLS Parameters
        self.dls_section = CollapsibleSection("DLS Parameters")
        dls_form = QFormLayout()
        self.sampling_rate = QDoubleSpinBox()
        self.sampling_rate.setRange(0.1, 1000.0)
        self.sampling_rate.setValue(10.0)
        self.sampling_rate.setSuffix(" kHz")
        dls_form.addRow("Sampling Rate:", self.sampling_rate)
        self.dls_section.content_layout.addLayout(dls_form)
        layout.addWidget(self.dls_section)
        self.sections.append(self.dls_section)

        for s in self.sections:
            s.toggled.connect(self.on_section_toggled)

        self.connect_btn = QPushButton("Connect devices")
        self.connect_btn.clicked.connect(self.on_connect_clicked)
        layout.addStretch()
        layout.addWidget(self.connect_btn)
        self.main_layout.addWidget(panel, 1, 0)

    def setup_control_panel(self):
        panel = QGroupBox("Execution Controls")
        layout = QVBoxLayout(panel)
        
        btn_layout = QHBoxLayout()
        self.start_btn = QPushButton("Start")
        self.stop_btn = QPushButton("Stop")
        self.start_btn.setStyleSheet("background-color: #2d5a27;")
        self.stop_btn.setStyleSheet("background-color: #7a2d2d;")
        self.stop_btn.setEnabled(False)
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.stop_btn)
        layout.addLayout(btn_layout)

        clock_layout = QHBoxLayout()
        eb = QGroupBox("Time elapsed")
        el = QVBoxLayout(eb)
        self.elapsed_lbl = QLabel("00:00:00")
        self.elapsed_lbl.setFont(QFont("Monospace", 20, QFont.Weight.Bold))
        self.elapsed_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        el.addWidget(self.elapsed_lbl)
        
        rb = QGroupBox("Time remaining")
        rl = QVBoxLayout(rb)
        self.remaining_lbl = QLabel("00:00:00")
        self.remaining_lbl.setFont(QFont("Monospace", 20, QFont.Weight.Bold))
        self.remaining_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        rl.addWidget(self.remaining_lbl)
        clock_layout.addWidget(eb)
        clock_layout.addWidget(rb)
        layout.addLayout(clock_layout)

        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)
        
        self.main_layout.addWidget(panel, 1, 1)

    def on_section_toggled(self, expanded):
        if not expanded: return
        sender = self.sender()
        for s in self.sections:
            if s != sender: s.set_expanded(False)

    def on_connect_clicked(self):
        dialog = ConnectionDialog(self, show_ni=True, show_ni_output=False)
        if dialog.exec():
            selection = dialog.get_selection()
            self.tfp_handler = TFPHandler(port=selection['tfp_port'])
            self.tfp_handler.connect()
            self.ni_handler = NIHandler(
                device_name=selection['ni_device'],
                counter_path=selection['ni_counter'],
                source_terminal=selection['ni_source']
            )
            self.ni_handler.connect()

    def on_back_clicked(self):
        from frontend.spectrometer_window import SpectrometerWindow
        self.sw = SpectrometerWindow()
        self.sw.show()
        self.close()

    def on_observe_clicked(self):
        self.observe_btn.setEnabled(False)
        self.stop_observe_btn.setEnabled(True)
        nb_channels = int(self.nb_channels_cb.currentText())
        self.observation_thread = QThread()
        self.observation_worker = TFPWorker(self.tfp_handler, expected_length=nb_channels)
        self.observation_worker.moveToThread(self.observation_thread)
        self.observation_thread.started.connect(self.observation_worker.run)
        self.observation_worker.data_received.connect(self.update_tfp_plot)
        self.observation_worker.finished.connect(self.observation_thread.quit)
        self.observation_thread.start()

    def on_stop_observing_clicked(self):
        if self.observation_worker: self.observation_worker.stop()
        self.observe_btn.setEnabled(True)
        self.stop_observe_btn.setEnabled(False)

    def update_tfp_plot(self, data):
        self.tfp_curve.setData(data)

    def closeEvent(self, event):
        if self.tfp_handler: self.tfp_handler.disconnect()
        if self.ni_handler: self.ni_handler.disconnect()
        super().closeEvent(event)
