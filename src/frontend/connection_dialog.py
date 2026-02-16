import sys
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
    QPushButton, QGroupBox, QFormLayout
)
from PyQt6.QtCore import Qt
import serial.tools.list_ports
try:
    import nidaqmx.system
    NI_AVAILABLE = True
except ImportError:
    NI_AVAILABLE = False

from backend.ni_handler import NIHandler

class ConnectionDialog(QDialog):
    def __init__(self, parent=None, show_ni=True):
        super().__init__(parent)
        self.setWindowTitle("Hardware Connection Management")
        self.setMinimumWidth(500)
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
                color: #e1e1e1;
            }
            QGroupBox {
                border: 1px solid #3d3d3d;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
                color: #007acc;
            }
            QLabel {
                color: #e1e1e1;
            }
            QComboBox {
                background-color: #3d3d3d;
                color: #e1e1e1;
                border: 1px solid #555;
                padding: 4px;
            }
            QPushButton {
                background-color: #3d3d3d;
                color: #e1e1e1;
                border-radius: 4px;
                padding: 6px 15px;
            }
            QPushButton#confirmBtn {
                background-color: #2d5a27;
            }
            QPushButton#cancelBtn {
                background-color: #7a2d2d;
            }
        """)

        self.layout = QVBoxLayout(self)
        self.ni_handler = NIHandler()
        self.show_ni = show_ni

        # Main Panels Layout
        self.panels_layout = QHBoxLayout()

        # --- TFP Panel ---
        self.tfp_group = QGroupBox("TFP")
        self.tfp_layout = QFormLayout(self.tfp_group)
        self.tfp_port_cb = QComboBox()
        self.refresh_ports()
        self.tfp_layout.addRow("Serial Port:", self.tfp_port_cb)
        self.panels_layout.addWidget(self.tfp_group)

        # --- NI Panel ---
        if self.show_ni:
            self.ni_group = QGroupBox("NI Device Configuration")
            self.ni_layout = QFormLayout(self.ni_group)
            
            self.ni_device_cb = QComboBox()
            self.ni_counter_cb = QComboBox()
            self.ni_source_cb = QComboBox()
            self.ni_output_cb = QComboBox()
            
            self.ni_device_cb.currentTextChanged.connect(self.update_ni_slots)
            
            self.refresh_ni_devices()
            
            self.ni_layout.addRow("Device/Module:", self.ni_device_cb)
            self.ni_layout.addRow("Counter Path:", self.ni_counter_cb)
            self.ni_layout.addRow("Source Terminal:", self.ni_source_cb)
            self.ni_layout.addRow("Output Terminal:", self.ni_output_cb)
            
            self.panels_layout.addWidget(self.ni_group)

        self.layout.addLayout(self.panels_layout)

        # --- Bottom Buttons ---
        self.btn_layout = QHBoxLayout()
        self.btn_layout.addStretch()
        
        self.confirm_btn = QPushButton("Confirm")
        self.confirm_btn.setObjectName("confirmBtn")
        self.confirm_btn.clicked.connect(self.accept)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setObjectName("cancelBtn")
        self.cancel_btn.clicked.connect(self.reject)
        
        self.btn_layout.addWidget(self.confirm_btn)
        self.btn_layout.addWidget(self.cancel_btn)
        self.layout.addLayout(self.btn_layout)

    def refresh_ports(self):
        self.tfp_port_cb.clear()
        ports = serial.tools.list_ports.comports()
        for port in ports:
            self.tfp_port_cb.addItem(port.device)
        if not ports:
            self.tfp_port_cb.addItem("No ports found")

    def refresh_ni_devices(self):
        self.ni_device_cb.clear()
        
        # Populate Device/Modules
        modules = self.ni_handler.list_modules()
        for mod in modules:
            self.ni_device_cb.addItem(mod)
            
        if not modules:
            self.ni_device_cb.addItem("No NI hardware found")

    def update_ni_slots(self, module_name):
        """Update counter and terminal options based on the selected module."""
        if not module_name or "No" in module_name:
            return
            
        self.ni_counter_cb.clear()
        self.ni_source_cb.clear()
        self.ni_output_cb.clear()
        
        # Counters
        counters = self.ni_handler.list_counters(module_name)
        for ctr in counters:
            self.ni_counter_cb.addItem(ctr)
            
        # Terminals (Source and Output)
        terminals = self.ni_handler.list_pfi_terminals(module_name)
        for term in terminals:
            self.ni_source_cb.addItem(term)
            self.ni_output_cb.addItem(term)

    def get_selection(self):
        ni_device = self.ni_device_cb.currentText() if self.show_ni else None
        ni_counter = self.ni_counter_cb.currentText() if self.show_ni else None
        ni_source = self.ni_source_cb.currentText() if self.show_ni else None
        ni_output = self.ni_output_cb.currentText() if self.show_ni else None

        return {
            "tfp_port": self.tfp_port_cb.currentText(),
            "ni_device": ni_device,
            "ni_counter": ni_counter,
            "ni_source": ni_source,
            "ni_output": ni_output
        }
