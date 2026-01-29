import sys
import unittest
from unittest.mock import MagicMock, patch
from PyQt6.QtWidgets import QApplication

# Mock PyQt6.QtWidgets.QMessageBox to avoid opening windows during automated tests
from PyQt6 import QtWidgets
QtWidgets.QMessageBox = MagicMock()

# Ensure we can import NIHandler
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.backend.ni_handler import NIHandler

class TestNIHandler(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # QApplication is needed for QMessageBox even if mocked
        cls.app = QApplication(sys.argv)

    def test_init_mock_mode(self):
        # If nidaqmx is not installed, it should default to mock mode
        handler = NIHandler()
        # We can't easily force NIDAQ_AVAILABLE to False here without complex patching,
        # but we can check if it behaves consistently.
        self.assertTrue(hasattr(handler, 'is_mock'))

    def test_connect_mock(self):
        handler = NIHandler()
        handler.is_mock = True
        result = handler.connect()
        self.assertTrue(result)
        self.assertTrue(handler.is_mock)

    def test_mock_measure(self):
        handler = NIHandler()
        handler.is_mock = True
        data = handler.measure_period(samples_to_collect=10)
        self.assertEqual(len(data), 10)
        self.assertAlmostEqual(data.mean(), 0.1, delta=0.01)

    def test_start_stop_pulse(self):
        handler = NIHandler()
        handler.is_mock = True
        # These should run without errors in mock mode
        handler.start_delayed_pulse(delay=0.1, pulse_width=0.05)
        handler.stop_delayed_pulse()
        self.assertTrue(True) # Reached here without exception

if __name__ == '__main__':
    unittest.main()
