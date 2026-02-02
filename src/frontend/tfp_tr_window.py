import sys
import numpy as np
from PyQt6.QtWidgets import (
    QMainWindow, QVBoxLayout, QHBoxLayout, QGridLayout, QWidget, 
    QPushButton, QLabel, QFrame, QLineEdit, QComboBox, QFormLayout, 
    QProgressBar, QGroupBox, QMessageBox, QSpinBox, QDoubleSpinBox,
    QFileDialog
)
import time
from PyQt6.QtCore import Qt, QTimer, QPointF
from PyQt6.QtGui import QFont
import pyqtgraph as pg

from frontend.connection_dialog import ConnectionDialog
from backend.tfp_handler import TFPHandler
from backend.ni_handler import NIHandler
from frontend.tfp_worker import TFPWorker
from frontend.experiment_worker import ExperimentWorker
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal

import matplotlib.pyplot as plt

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

    def is_expanded(self):
        return self.toggle_button.isChecked()

class TFP_TRWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Time-resolved TFP Interface")
        self.setMinimumSize(1000, 800)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
            }
            QGroupBox {
                border: 2px solid #3d3d3d;
                border-radius: 8px;
                margin-top: 1ex;
                padding: 10px;
                background-color: #252526;
                color: #e1e1e1;
                font-weight: bold;
            }
            QLabel {
                color: #e1e1e1;
            }
            QPushButton {
                background-color: #3d3d3d;
                color: #e1e1e1;
                border-radius: 4px;
                padding: 8px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #505050;
            }
            QLineEdit, QComboBox {
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
            QProgressBar::chunk {
                background-color: #007acc;
            }
        """)

        # Central widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QGridLayout(self.central_widget)
        self.main_layout.setSpacing(15)

        # Initialize handlers
        self.tfp_handler = TFPHandler() # Default handler for observation
        self.ni_handler = NIHandler()
        
        # Channel selection state
        self.scanned_channels = []  # List of (min_freq, max_freq) tuples
        self.channel_regions = []   # List of pg.LinearRegionItem
        self.interaction_mode = None # 'add' or 'remove'
        self.drag_start_x = None
        self.temp_region = None
        self.nb_cycles = 1
        self.time_around_pulse_ms = 1.0
        self.delays = None
        self.results = None
        
        self.observation_thread = None
        self.observation_worker = None
        
        self.experiment_thread = None
        self.experiment_worker = None

        # Timing variables
        self.experiment_start_time = 0
        self.total_duration_estimate = 0
        self.clock_timer = QTimer()
        self.clock_timer.timeout.connect(self.update_clocks)

        # --- Top Left: Histogram / Observe Panel ---
        self.setup_top_left_panel()

        # --- Top Right: Heatmap / Image Panel ---
        self.setup_top_right_panel()

        # --- Bottom Left: Parameters Panel ---
        self.setup_bottom_left_panel()

        # --- Bottom Right: Control Panel ---
        self.setup_bottom_right_panel()

        # Bottom Buttons Layout
        bottom_buttons_layout = QHBoxLayout()
        
        # Back button
        self.back_btn = QPushButton("Back to Spectrometer choice")
        self.back_btn.setStyleSheet("background-color: #3d3d3d; font-weight: bold;")
        self.back_btn.clicked.connect(self.on_back_clicked)
        bottom_buttons_layout.addWidget(self.back_btn)

        # Close button
        self.close_btn = QPushButton("Close Application")
        self.close_btn.setStyleSheet("background-color: #7a2d2d; font-weight: bold;")
        self.close_btn.clicked.connect(self.close)
        bottom_buttons_layout.addWidget(self.close_btn)

        self.main_layout.addLayout(bottom_buttons_layout, 2, 0, 1, 2)

    def on_back_clicked(self):
        """Go back to the spectrometer window after disconnecting hardware."""
        from frontend.spectrometer_window import SpectrometerWindow
        self.spectrometer_window = SpectrometerWindow()
        self.spectrometer_window.show()
        # self.close() will trigger closeEvent and disconnect hardware
        self.close()

    def setup_top_left_panel(self):
        panel = QGroupBox("Signal Observation")
        layout = QVBoxLayout(panel)

        # Variable storing the number of samples on the graph
        self.nb_samples = 0

        # Plot
        self.hist_plot = pg.PlotWidget(title="Counts vs Frequency shift")
        self.hist_plot.setBackground('#1e1e1e')
        self.hist_plot.setLabel('left', 'Counts', units='')
        self.hist_plot.setLabel('bottom', 'Frequency shift', units='Hz')
        self.hist_plot.showGrid(x=True, y=True, alpha=0.3)
        self.hist_plot.setCursor(Qt.CursorShape.CrossCursor)
        self.cursor_line = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen('w', style=Qt.PenStyle.DashLine))
        self.cursor_line.hide()
        self.hist_plot.addItem(self.cursor_line)
        self.hist_curve = self.hist_plot.plot(pen=pg.mkPen(color='#007acc', width=1))
        layout.addWidget(self.hist_plot)

        # Buttons
        btn_layout = QHBoxLayout()
        self.observe_btn = QPushButton("Observe")
        self.stop_observe_btn = QPushButton("Stop observing")
        self.stop_observe_btn.setEnabled(False) # Disabled at initialization
        
        self.observe_btn.clicked.connect(self.on_observe_clicked)
        self.stop_observe_btn.clicked.connect(self.on_stop_observing_clicked)
        
        btn_layout.addWidget(self.observe_btn)
        btn_layout.addWidget(self.stop_observe_btn)
        layout.addLayout(btn_layout)

        # Connect plot interactions
        # We'll use an event filter for robust drag-to-create handling
        self.hist_plot.viewport().installEventFilter(self)
        self.temp_region = None
        self.drag_start_x = None

        self.main_layout.addWidget(panel, 0, 0)

    def setup_top_right_panel(self):
        panel = QGroupBox("Experiment Status")
        layout = QVBoxLayout(panel)

        # Heatmap / Image
        self.heatmap_plot = pg.PlotWidget(title="Delay vs Channels")
        self.heatmap_plot.setBackground('#1e1e1e')
        self.heatmap_plot.setLabel('left', 'Delay')
        self.heatmap_plot.setLabel('bottom', 'Channels')
        
        self.image_item = pg.PColorMeshItem()
        self.heatmap_plot.addItem(self.image_item)
        
        # Dummy data for visualization
        # With PColorMeshItem, we use setData(x, y, z)
        # Initialize with dummy X, Y, Z for a 10x10 grid
        x_dummy = np.arange(11)
        y_dummy = np.arange(11)
        X_mesh, Y_mesh = np.meshgrid(x_dummy, y_dummy)
        self.image_item.setData(X_mesh, Y_mesh, np.zeros((10, 10)))
        
        # Custom LUT for the heatmap
        # self.lut = pg.HistogramLUTWidget()
        # self.lut.setImageItem(self.image_item)
        # self.lut.setBackground('#1e1e1e')
        
        plot_layout = QHBoxLayout()
        plot_layout.addWidget(self.heatmap_plot)
        # plot_layout.addWidget(self.lut) # Commented out as lut is not used with ImageItem directly here
        layout.addLayout(plot_layout)

        self.main_layout.addWidget(panel, 0, 1)

    def setup_bottom_left_panel(self):
        panel = QGroupBox("Experiment Parameters")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(5, 15, 5, 5)
        panel_layout.setSpacing(5)

        self.sections = []

        # --- Section 1: Chosen channels ---
        self.channels_section = CollapsibleSection("Chosen channels")
        self.add_channels_btn = QPushButton("Add channels")
        self.remove_channels_btn = QPushButton("Remove channels")
        self.channels_section.content_layout.addWidget(self.add_channels_btn)
        self.channels_section.content_layout.addWidget(self.remove_channels_btn)
        
        self.add_channels_btn.setCheckable(True)
        self.remove_channels_btn.setCheckable(True)

        self.add_channels_btn.clicked.connect(self.toggle_add_mode)
        self.remove_channels_btn.clicked.connect(self.toggle_remove_mode)
        self.remove_channels_btn.setEnabled(False)
        
        panel_layout.addWidget(self.channels_section)
        self.sections.append(self.channels_section)

        # --- Section 2: Stimulation synchronized parameters ---
        self.delay_section = CollapsibleSection("Stimulation synchronized parameters")
        stim_form = QFormLayout()
        
        self.cycles_spin = QSpinBox()
        self.cycles_spin.setRange(1, 1000000)
        self.cycles_spin.setValue(1)
        self.cycles_spin.setSingleStep(1)
        self.cycles_spin.valueChanged.connect(self.on_cycles_changed)
        
        stim_form.addRow("Number of cycles:", self.cycles_spin)
        
        self.time_around_pulse_spin = QDoubleSpinBox()
        self.time_around_pulse_spin.setRange(0.5, 1000.0)
        self.time_around_pulse_spin.setSingleStep(0.5)
        self.time_around_pulse_spin.setValue(1.0)
        self.time_around_pulse_spin.setSuffix(" ms")
        self.time_around_pulse_spin.valueChanged.connect(self.on_time_around_pulse_changed)
        
        stim_form.addRow("Experiment duration (centered on pulse, in ms):", self.time_around_pulse_spin)
        self.delay_section.content_layout.addLayout(stim_form)
        
        panel_layout.addWidget(self.delay_section)
        self.sections.append(self.delay_section)

        # --- Section 3: TFP channel frequency ---
        self.tfp_freq_section = CollapsibleSection("TFP channel frequency")
        tfp_form = QFormLayout()
        
        self.wavelength = QLineEdit()
        self.wavelength.setPlaceholderText("nm")
        self.wavelength.editingFinished.connect(self.update_tfp_frequency_axis)
        
        self.mirror_spacing = QLineEdit()
        self.mirror_spacing.setPlaceholderText("mm")
        self.mirror_spacing.editingFinished.connect(self.update_tfp_frequency_axis)
        
        self.scanning_range = QLineEdit()
        self.scanning_range.setPlaceholderText("nm")
        self.scanning_range.editingFinished.connect(self.update_tfp_frequency_axis)

        tfp_form.addRow("Wavelength (nm):", self.wavelength)
        tfp_form.addRow("Mirror spacing (mm):", self.mirror_spacing)
        tfp_form.addRow("Scanning range (nm):", self.scanning_range)
        self.tfp_freq_section.content_layout.addLayout(tfp_form)
        
        panel_layout.addWidget(self.tfp_freq_section)
        self.sections.append(self.tfp_freq_section)

        # Mutual exclusivity logic
        for section in self.sections:
            section.toggled.connect(self.on_section_toggled)

        # Fixed Button: Connect devices
        self.connect_devices_btn = QPushButton("Connect devices")
        self.connect_devices_btn.clicked.connect(self.on_connect_devices)
        panel_layout.addStretch()
        panel_layout.addWidget(self.connect_devices_btn)

        self.main_layout.addWidget(panel, 1, 0)

    def on_cycles_changed(self, value):
        self.nb_cycles = value
        print(f"Number of cycles updated: {self.nb_cycles}")
        self.estimate_duration()

    def on_time_around_pulse_changed(self, value):
        self.time_around_pulse_ms = value
        print(f"Time around pulse updated: {self.time_around_pulse_ms} ms")
        self.estimate_duration()

    def on_section_toggled(self, is_expanded):
        if not is_expanded:
            return
        
        sender = self.sender()
        for section in self.sections:
            if section != sender:
                section.set_expanded(False)

    def toggle_add_mode(self, checked):
        if checked:
            self.interaction_mode = 'add'
            self.remove_channels_btn.setChecked(False)
            self.add_channels_btn.setStyleSheet("background-color: #007acc; font-weight: bold;")
            self.remove_channels_btn.setStyleSheet("")
            if self.remove_channels_btn.isEnabled():
                 self.remove_channels_btn.setStyleSheet("background-color: #3d3d3d; color: #e1e1e1;")
            self.hist_plot.setCursor(Qt.CursorShape.BlankCursor)
            self.cursor_line.show()
        else:
            self.interaction_mode = None
            self.add_channels_btn.setStyleSheet("")
            self.hist_plot.setCursor(Qt.CursorShape.CrossCursor)
            self.cursor_line.hide()
        
        self.update_region_interactivity()

    def toggle_remove_mode(self, checked):
        if checked:
            self.interaction_mode = 'remove'
            self.add_channels_btn.setChecked(False)
            self.remove_channels_btn.setStyleSheet("background-color: #7a2d2d; font-weight: bold;")
            self.add_channels_btn.setStyleSheet("")
            self.hist_plot.setCursor(Qt.CursorShape.CrossCursor)
        else:
            self.interaction_mode = None
            self.remove_channels_btn.setStyleSheet("")
            if self.remove_channels_btn.isEnabled():
                self.remove_channels_btn.setStyleSheet("background-color: #3d3d3d; color: #e1e1e1;")
            self.hist_plot.setCursor(Qt.CursorShape.CrossCursor)
        
        self.update_region_interactivity()

    def update_region_interactivity(self):
        """Enable or disable region movement/resizing based on interaction mode."""
        is_interactive = (self.interaction_mode is None)
        for region in self.channel_regions:
            region.setMovable(is_interactive)

    def eventFilter(self, source, event):
        if source == self.hist_plot.viewport():
            if self.interaction_mode == 'add':
                if event.type() == event.Type.MouseButtonPress:
                    if event.button() == Qt.MouseButton.LeftButton:
                        pos = event.scenePosition()
                        mouse_point = self.hist_plot.plotItem.vb.mapSceneToView(pos)
                        self.drag_start_x = mouse_point.x()

                        self.temp_region = pg.LinearRegionItem(
                            values=[self.drag_start_x, self.drag_start_x],
                            brush=pg.mkBrush(255, 0, 0, 80),
                            pen=pg.mkPen('r', width=2)
                        )
                        self.hist_plot.addItem(self.temp_region)
                        return True
                
                elif event.type() == event.Type.MouseMove:
                    pos = event.scenePosition()
                    mouse_point = self.hist_plot.plotItem.vb.mapSceneToView(pos)
                    current_x = mouse_point.x()
                    
                    # Always update cursor line in add mode
                    self.cursor_line.setPos(current_x)
                    
                    if self.drag_start_x is not None and self.temp_region:
                        low = min(self.drag_start_x, current_x)
                        high = max(self.drag_start_x, current_x)
                        self.temp_region.setRegion([low, high])
                    return True
                
                elif event.type() == event.Type.MouseButtonRelease:
                    if self.drag_start_x is not None:
                        if self.temp_region:
                            # Finalize current temp region
                            self.channel_regions.append(self.temp_region)
                            self.merge_regions()
                        self.drag_start_x = None
                        self.temp_region = None
                        return True
            
            elif self.interaction_mode == 'remove':
                if event.type() == event.Type.MouseButtonPress:
                    pos = event.scenePosition()
                    mouse_point = self.hist_plot.plotItem.vb.mapSceneToView(pos)
                    x = mouse_point.x()
                    
                    found = False
                    for region in self.channel_regions[:]:
                        low, high = region.getRegion()
                        if min(low, high) <= x <= max(low, high):
                            self.hist_plot.removeItem(region)
                            self.channel_regions.remove(region)
                            found = True
                    
                    if found:
                        self.update_scanned_channels_list()
                        return True

        return super().eventFilter(source, event)

    def merge_regions(self):
        """Sorts and merges overlapping regions on the plot."""
        if not self.channel_regions:
            self.update_scanned_channels_list()
            return

        # Get current regions, sort by start values
        intervals = []
        for r in self.channel_regions:
            low, high = r.getRegion()
            intervals.append((min(low, high), max(low, high)))
        
        intervals.sort(key=lambda x: x[0])
        
        merged = []
        if intervals:
            curr_start, curr_end = intervals[0]
            for next_start, next_end in intervals[1:]:
                if next_start <= curr_end:
                    curr_end = max(curr_end, next_end)
                else:
                    merged.append((curr_start, curr_end))
                    curr_start, curr_end = next_start, next_end
            merged.append((curr_start, curr_end))

        # Re-create regions only if the count or intervals changed to avoid flickering during resize
        # But for simplicity and ensuring "one region on the graph", let's redraw
        for r in self.channel_regions:
            self.hist_plot.removeItem(r)
        self.channel_regions.clear()

        for low, high in merged:
            region = pg.LinearRegionItem(
                values=[low, high],
                brush=pg.mkBrush(255, 0, 0, 80),
                pen=pg.mkPen('r', width=2),
                movable=(self.interaction_mode is None)
            )
            self.hist_plot.addItem(region)
            self.channel_regions.append(region)
            # Use sigRegionChangeFinished for manual resize to merge after release
            region.sigRegionChangeFinished.connect(self.merge_regions)

        self.update_scanned_channels_list()
        self.estimate_duration()

    def update_scanned_channels_list(self):
        """Synchronize scanned_channels list with current plot regions."""
        self.scanned_channels = [r.getRegion() for r in self.channel_regions]
        print(f"Scanned channels updated: {self.scanned_channels}")
        
        # Enable/Disable "Remove channels" button
        has_regions = len(self.channel_regions) > 0
        self.remove_channels_btn.setEnabled(has_regions)
        
        if not has_regions:
            if self.remove_channels_btn.isChecked():
                self.remove_channels_btn.setChecked(False)
                self.toggle_remove_mode(False)
            self.remove_channels_btn.setStyleSheet("background-color: #2a2a2a; color: #555;") # Visually disabled
        else:
            if not self.remove_channels_btn.isChecked():
                self.remove_channels_btn.setStyleSheet("background-color: #3d3d3d; color: #e1e1e1;")

    def setup_bottom_right_panel(self):
        panel = QGroupBox("Execution Controls")
        layout = QVBoxLayout(panel)

        # Execution Buttons
        btn_layout = QHBoxLayout()
        self.start_btn = QPushButton("Start")
        self.stop_btn = QPushButton("Stop")
        self.realign_btn = QPushButton("Realign")
        
        self.stop_btn.setEnabled(False)
        self.realign_btn.setEnabled(False)
        
        # Style specific for start/stop
        self.start_btn.setStyleSheet("background-color: #2d5a27;")
        self.stop_btn.setStyleSheet("background-color: #7a2d2d;")
        
        self.start_btn.clicked.connect(self.start_measure)
        self.stop_btn.clicked.connect(self.abort_measure)
        self.realign_btn.clicked.connect(self.pause_measure)
        
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.stop_btn)
        btn_layout.addWidget(self.realign_btn)
        layout.addLayout(btn_layout)

        # Clocks
        clock_layout = QHBoxLayout()
        
        elapsed_box = QGroupBox("Time elapsed")
        elapsed_layout = QVBoxLayout(elapsed_box)
        self.time_elapsed_label = QLabel("00:00:00")
        self.time_elapsed_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_elapsed_label.setFont(QFont("Monospace", 20, QFont.Weight.Bold))
        elapsed_layout.addWidget(self.time_elapsed_label)
        
        remaining_box = QGroupBox("Time remaining")
        remaining_layout = QVBoxLayout(remaining_box)
        self.time_remaining_label = QLabel("00:00:00")
        self.time_remaining_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_remaining_label.setFont(QFont("Monospace", 20, QFont.Weight.Bold))
        remaining_layout.addWidget(self.time_remaining_label)
        
        clock_layout.addWidget(elapsed_box)
        clock_layout.addWidget(remaining_box)
        layout.addLayout(clock_layout)

        # Progress
        progress_layout = QVBoxLayout()
        self.progress_label = QLabel("Progress: 0%")
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_label)
        progress_layout.addWidget(self.progress_bar)
        layout.addLayout(progress_layout)

        self.main_layout.addWidget(panel, 1, 1)

    def on_connect_devices(self):
        dialog = ConnectionDialog(self)
        if dialog.exec():
            selection = dialog.get_selection()
            print(f"Connecting to TFP on {selection['tfp_port']} and NI device {selection['ni_device']}")
            
            # Initialize handlers
            self.tfp_handler = TFPHandler(port=selection['tfp_port'])
            if self.tfp_handler.connect():
                print("TFP Handler initialized and connected.")
            
            # Extract NI configuration from selection
            ni_device = selection['ni_device']
            ni_counter = selection['ni_counter']
            ni_source = selection['ni_source']
            ni_output = selection['ni_output']
            
            print(f"NI Configuration: Device={ni_device}, Counter={ni_counter}, Source={ni_source}, Output={ni_output}")
            
            self.ni_handler = NIHandler(
                device_name=ni_device,
                counter_path=ni_counter,
                source_terminal=ni_source,
                output_terminal=ni_output
            )
            
            if self.ni_handler.connect():
                print("NI Handler initialized and connected.")

    def closeEvent(self, event):
        """Ensure hardware is disconnected before closing."""
        print("Closing application. Disconnecting hardware...")
        if self.tfp_handler:
            self.tfp_handler.disconnect()
        if self.ni_handler:
            self.ni_handler.disconnect()
        time.sleep(0.2) # Wait for the serial connection to close
        event.accept()

    def on_observe_clicked(self):
        """Start continuous observation."""
        self.observe_btn.setEnabled(False)
        self.stop_observe_btn.setEnabled(True)

        self.observation_thread = QThread()
        self.observation_worker = TFPWorker(self.tfp_handler)
        self.observation_worker.moveToThread(self.observation_thread)

        self.observation_thread.started.connect(self.observation_worker.run)
        self.observation_worker.data_received.connect(self.update_hist_plot)
        self.observation_worker.finished.connect(self.observation_thread.quit)
        self.observation_worker.finished.connect(self.observation_worker.deleteLater)
        self.observation_thread.finished.connect(self.observation_thread.deleteLater)

        self.observation_thread.start()

    def on_stop_observing_clicked(self):
        """Stop continuous observation."""
        if self.observation_worker:
            self.observation_worker.stop()
        
        self.observe_btn.setEnabled(True)
        self.stop_observe_btn.setEnabled(False)

    def update_hist_plot(self, data):
        """Update the top left plot with new scan data using the frequency axis."""
        self.nb_samples = len(data)
        x_axis = self.tfp_handler.freq_axis_func(self.nb_samples)
        self.hist_curve.setData(x_axis, data)

    def update_tfp_frequency_axis(self):
        """Update the frequency axis logic in the handler based on user input."""
        try:
            lmbda = float(self.wavelength.text()) if self.wavelength.text() else None
            mirror_spacing = float(self.mirror_spacing.text()) if self.mirror_spacing.text() else None
            scan_range = float(self.scanning_range.text()) if self.scanning_range.text() else None
            
            # Note: Wavelength is in nm (no convert), mirror spacing mm (no convert), scan range µm (no convert)
            # The backend expected nm, mm, µm respectively based on the labels.
            old_x = self.tfp_handler.freq_axis_func(self.nb_samples)
            self.tfp_handler.frequency_axis(
                lmbda=lmbda, 
                mirror_spacing=mirror_spacing, 
                scan_range=scan_range
            )
            new_x = self.tfp_handler.freq_axis_func(self.nb_samples)

            new_scanned_channels = []
            for chan in self.scanned_channels:
                x0 = new_x[np.argmin(np.abs(old_x - chan[0]))]
                xf = new_x[np.argmin(np.abs(old_x - chan[1]))]
                new_scanned_channels.append([x0, xf])
            self.scanned_channels = new_scanned_channels

            for region in self.channel_regions[:]:
                self.hist_plot.removeItem(region)
                self.channel_regions.remove(region)

            for chan in self.scanned_channels:
                region = pg.LinearRegionItem(values=chan,
                                             brush=pg.mkBrush(255, 0, 0, 80),
                                             pen=pg.mkPen('r', width=2))
                self.hist_plot.addItem(region)
                self.channel_regions.append(region)

            print(f"Frequency axis updated: lambda={lmbda}, spacing={mirror_spacing}, range={scan_range}")
            self.estimate_duration()
        except ValueError:
            # Ignore invalid input
            pass

    def on_range_around_stim_changed(self):
        """Validates that the stimulation range is a multiple of the quantum."""
        text = self.range_around_stim.text()
        if not text:
            return
            
        try:
            value = float(text)
            validated_value, was_updated = self.tfp_handler.validate_stimulation_range(value)
            
            if was_updated:
                self.range_around_stim.setText(f"{validated_value:.2f}")
                QMessageBox.information(
                    self,
                    "Parameter Adjusted",
                    f"The stimulation range has been adjusted to {validated_value:.2f} ms "
                    f"to be a multiple of {self.tfp_handler.SCAN_STEP_QUANTUM} ms (250 µs)."
                )
        except ValueError:
            # Revert or ignore invalid numeric input
            pass

    def estimate_duration(self):
        """Estimates the duration of the experiment and updates the remaining time label."""

        if not hasattr(self, 'time_remaining_label'):
            return

        total_seconds = self.tfp_handler.estimate_duration(self.scanned_channels, self.nb_samples, self.time_around_pulse_ms, self.nb_cycles)
        self.total_duration_estimate = total_seconds
        print("Total seconds: ", total_seconds)
        
        # Format as HH:MM:SS
        self.time_remaining_label.setText(self.format_time(total_seconds))

    def format_time(self, total_seconds):
        """Formats seconds into HH:MM:SS string."""
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        seconds = int(total_seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def update_clocks(self):
        """Updates the elapsed and remaining time labels."""
        if self.experiment_start_time == 0:
            return
            
        elapsed = time.time() - self.experiment_start_time
        remaining = max(0, self.total_duration_estimate - elapsed)
        
        self.time_elapsed_label.setText(self.format_time(elapsed))
        self.time_remaining_label.setText(self.format_time(remaining))

    def start_measure(self):
        """Starts the measurement process."""
        # Stop observation if running
        if self.observation_thread and self.observation_thread.isRunning():
            self.on_stop_observing_clicked()
            print("Observation stopped to start measurement.")

        if len(self.channel_regions) == 0:
            QMessageBox.warning(
                self,
                "Measurement Error",
                "No windows selected. Please select at least one window."
            )
            return
            
        elif len(self.channel_regions) == 1:
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.realign_btn.setEnabled(True)

            chan = self.scanned_channels[0]
            low, high = chan
            freq = self.tfp_handler.freq_axis_func(self.nb_samples)

            idx0 = np.argmin(np.abs(freq - low)) # Time index gotten by multiplying by 0.5ms
            idx1 = np.argmin(np.abs(freq - high))

            idx0 = idx0*0.5 - self.time_around_pulse_ms//2
            idx1 = idx1*0.5 + self.time_around_pulse_ms//2

            self.delays = np.arange(idx0, idx1 + 1, 0.5) # Delays of pulse in ms
        
            # Create thread and worker
            self.experiment_thread = QThread()
            self.experiment_worker = ExperimentWorker(
                self.tfp_handler, 
                self.ni_handler, 
                self.delays, 
                self.nb_cycles,
                spectrum_len=self.nb_samples
            )
            self.experiment_worker.moveToThread(self.experiment_thread)
            
            # Connect signals
            self.experiment_thread.started.connect(self.experiment_worker.run)
            self.experiment_worker.progress_updated.connect(self.on_experiment_progress)
            self.experiment_worker.data_received.connect(self.update_hist_plot)
            self.experiment_worker.results_updated.connect(self.update_heatmap)
            self.experiment_worker.results_ready.connect(self.on_experiment_results_ready)
            self.experiment_worker.error.connect(self.on_experiment_error)
            self.experiment_worker.finished.connect(self.on_experiment_finished)
            self.experiment_worker.finished.connect(self.experiment_thread.quit)
            self.experiment_worker.finished.connect(self.experiment_worker.deleteLater)
            self.experiment_thread.finished.connect(self.experiment_thread.deleteLater)
            
            # Start clocks
            self.experiment_start_time = time.time()
            self.clock_timer.start(1000) # Update every second

            # Start
            self.experiment_thread.start()

        else:
            QMessageBox.warning(
                self,
                "Measurement Error",
                "Multiple windows are not supported yet. Please select only one window."
            )
            return

    def abort_measure(self):
        """Aborts the measurement process."""
        if self.experiment_worker:
            self.experiment_worker.stop()
        
        if self.experiment_thread and self.experiment_thread.isRunning():
            self.experiment_thread.quit()
            self.experiment_thread.wait()

        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.realign_btn.setEnabled(False)
        self.realign_btn.setText("Realign") # Ensure it's reset
        
        # Stop clocks
        self.clock_timer.stop()
        self.experiment_start_time = 0
        
        # Reset UI elements
        self.progress_bar.setValue(0)
        self.progress_label.setText("Progress: 0%")
        self.time_elapsed_label.setText("00:00:00")
        self.estimate_duration() # Restore estimated remaining time
        
        print("Measurement aborted.")

    def on_experiment_progress(self, progress, status_text):
        """Update UI with experiment progress."""
        self.progress_bar.setValue(progress)
        self.progress_label.setText(f"Progress: {progress}% - {status_text}")

    def on_experiment_results_ready(self, results, delay_array):
        """Handle final results from experiment worker."""
        self.results = results
        self.delay_array = delay_array
        print("Measurement results received.")
        self.save_results()

    def save_results(self):
        """Prompts the user to save the experiment results in HDF5_BLS format."""
        if self.results is None:
            return

        try:
            from frontend.hdf5_save_dialog import HDF5SaveDialog
            from HDF5_BLS import Wrapper
        except ImportError as e:
            QMessageBox.critical(self, "Import Error", f"Failed to load HDF5_BLS or saving dialog: {e}")
            return

        dialog = HDF5SaveDialog(self)
        if dialog.exec():
            selection = dialog.get_selection()
            file_path = selection["file_path"]
            target_group = selection["selected_group"]

            if file_path:
                try:
                    wrp = Wrapper(file_path)
                    
                    # Prepare datasets
                    freq = self.tfp_handler.freq_axis_func(self.nb_samples)
                    
                    # Store datasets in the chosen group
                    wrp.add_frequency(freq, target_group, name="Frequency")
                    wrp.add_abscissa(self.delay_array, target_group, name="Delays")
                    wrp.add_PSD(self.results, target_group, name="PSD")
                    
                    # Add attributes
                    wrp.add_attributes({"SPECTROMETER.Type": "TFP"}, parent_group=target_group)
                    
                    wrp.close()
                    print(f"Results saved to {file_path} in group {target_group}")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to save results: {e}")

        freq = self.tfp_handler.freq_axis_func(self.nb_samples) * 1e-9

        channels = np.tile(freq[np.newaxis, :], (self.delay_array.shape[0], 1))

        plt.pcolormesh(self.delay_array, channels, self.results)
        
        plt.colorbar()
        plt.show()

    def update_heatmap(self, results, delay_array):
        """Update the 2D heatmap with cumulative experiment data."""
        if results is None or delay_array is None:
            return
            
        # Get frequency axis
        freq = self.tfp_handler.freq_axis_func(results.shape[1])
        
        # Add one last value with same values as last one
        freq = np.append(freq, 2*freq[-1] - freq[-2])
        
        # Prepare X (Frequency) and Y (Time Delay)
        # Frequency is constant per column in results
        # Time Delay (delay_array) varies per point
        
        X = np.tile(freq[np.newaxis, :], (results.shape[0]+1, 1))
        Y = np.zeros((delay_array.shape[0]+1, delay_array.shape[1]+1))
        Y[:-1, :-1] = delay_array
        Y[-1, :-1] = Y[-2, :-1] + 0.5
        Y[:, -1] = Y[:, -2] + 0.5

        
        # Update the PColorMeshItem
        # setData expects (X, Y, Z) where Z is the values
        try:
            self.image_item.setData(X, Y, results)
        except Exception as e:
            print(f"Heatmap update error: {e}")
        
        # Ensure plot labels are correct
        self.heatmap_plot.setLabel('bottom', 'Frequency Shift', units='Hz')
        self.heatmap_plot.setLabel('left', 'Time relative to pulse', units='ms')

    def tfp_handlers(self):
        # Small helper to get the right handler
        return self.tfp_handler

    def on_experiment_error(self, message):
        """Handle errors from experiment worker."""
        QMessageBox.critical(self, "Measurement Error", f"An error occurred: {message}")

    def on_experiment_finished(self):
        """Clean up UI after experiment finishes."""
        if self.experiment_worker and not self.experiment_worker._running:
             # Only reset if we finished normally or aborted
             self.abort_measure()
       
    def pause_measure(self):
        """Toggles between realign and measure."""
        if self.realign_btn.text() == "Realign":
            self.realign_btn.setText("go back to measure")
            self.stop_btn.setEnabled(False)
            print("Measurement paused for realignment.")
        else:
            self.realign_btn.setText("Realign")
            self.stop_btn.setEnabled(True)
            print("Measurement resumed.")