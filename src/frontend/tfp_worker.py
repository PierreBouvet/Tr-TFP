from PyQt6.QtCore import QObject, pyqtSignal, QThread
import time

class TFPWorker(QObject):
    data_received = pyqtSignal(list)
    finished = pyqtSignal()

    def __init__(self, tfp_handler):
        super().__init__()
        self.tfp_handler = tfp_handler
        self._running = False

    def run(self):
        self._running = True
        # If the handler is not connected, it will use the mock data generator 
        # as implemented in the observe method.
        for scan_data in self.tfp_handler.observe():
            if not self._running:
                break
            self.data_received.emit(scan_data)
        
        self.finished.emit()

    def stop(self):
        self._running = False
        self.tfp_handler.stop_observation()
