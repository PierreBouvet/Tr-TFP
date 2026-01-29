import sys
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QMessageBox, QFrame)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QFont

class SpectrometerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Spectrometer")
        self.setMinimumSize(600, 400)
        
        # Central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(40, 40, 40, 40)

        # Title
        title_label = QLabel("A new TFP interface")
        title_font = QFont("Inter UI", 24, QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)

        # Panes Layout
        panes_layout = QHBoxLayout()
        panes_layout.setSpacing(30)

        # Pane 1: TFP time-invariant measures
        self.btn_invariant = self.create_pane("TFP time-invariant measures", 
                                              "Analyze materials in a time-invariant manner.")
        self.btn_invariant.clicked.connect(self.on_invariant_clicked)
        panes_layout.addWidget(self.btn_invariant)

        # Pane 2: TFP time-resolved measures
        self.btn_resolved = self.create_pane("TFP time-resolved measures", 
                                             "Performs measurements by tagging each measure to a delay after a pulse.")
        self.btn_resolved.clicked.connect(self.on_resolved_clicked)
        panes_layout.addWidget(self.btn_resolved)

        main_layout.addLayout(panes_layout)
        
        # Apply some premium styling
        self.setStyleSheet("""
            QMainWindow {
                background-color: #121212;
            }
            QLabel {
                color: #E0E0E0;
            }
            QPushButton#PaneButton {
                background-color: #1E1E1E;
                border: 2px solid #333333;
                border-radius: 12px;
                color: #FFFFFF;
                padding: 20px;
                text-align: center;
            }
            QPushButton#PaneButton:hover {
                background-color: #2A2A2A;
                border-color: #007AFF;
            }
            QPushButton#PaneButton QLabel#Title {
                font-size: 18px;
                font-weight: bold;
                color: #007AFF;
            }
            QPushButton#PaneButton QLabel#Description {
                font-size: 14px;
                color: #BBBBBB;
            }
        """)

    def create_pane(self, title, description):
        button = QPushButton()
        button.setObjectName("PaneButton")
        button.setFixedSize(250, 200)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        
        layout = QVBoxLayout(button)
        
        title_lbl = QLabel(title)
        title_lbl.setObjectName("Title")
        title_lbl.setWordWrap(True)
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        desc_lbl = QLabel(description)
        desc_lbl.setObjectName("Description")
        desc_lbl.setWordWrap(True)
        desc_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(title_lbl)
        layout.addWidget(desc_lbl)
        
        return button

    def on_invariant_clicked(self):
        QMessageBox.information(self, "Not implemented yet", "The TFP time-invariant measures module is under development.")

    def on_resolved_clicked(self):
        from frontend.tfp_tr_window import TFP_TRWindow
        self.main_viewer = TFP_TRWindow()
        self.main_viewer.show()
        self.close()
