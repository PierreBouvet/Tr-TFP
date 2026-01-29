import unittest
import os
import sys

# Ensure we can import TFPHandler
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.backend.tfp_handler import TFPHandler

class TestTFPHandlerValidation(unittest.TestCase):
    def setUp(self):
        self.handler = TFPHandler()
        self.quantum = self.handler.SCAN_STEP_QUANTUM

    def test_multiples(self):
        # Already multiples - should not be updated
        self.assertEqual(self.handler.validate_stimulation_range(0.25), (0.25, False))
        self.assertEqual(self.handler.validate_stimulation_range(0.50), (0.50, False))
        self.assertEqual(self.handler.validate_stimulation_range(1.0), (1.0, False))

    def test_rounding_up(self):
        # Not multiples - should be rounded up
        self.assertEqual(self.handler.validate_stimulation_range(0.1), (0.25, True))
        self.assertEqual(self.handler.validate_stimulation_range(0.3), (0.50, True))
        self.assertEqual(self.handler.validate_stimulation_range(0.6), (0.75, True))

    def test_zero_and_negative(self):
        # Edge cases
        self.assertEqual(self.handler.validate_stimulation_range(0), (0.0, False))
        self.assertEqual(self.handler.validate_stimulation_range(-1.0), (0.0, False))

if __name__ == '__main__':
    unittest.main()
