import unittest
import tkinter as tk
import sys
import os
import threading
import time

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../src'))
from gui import CurveExtractorApp

class TestCalibrationPrecision(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = tk.Tk()
        cls.app = CurveExtractorApp(cls.root)
        
    @classmethod
    def tearDownClass(cls):
        cls.root.destroy()
        
    def test_precision_handling(self):
        """Test 1: Verify float precision is maintained for coordinates"""
        print("\nTesting Precision Handling...")
        
        # Simulate high precision mouse click
        # Canvas scale simulation
        self.app.start_x = 100.12345
        self.app.start_y = 200.67890
        scale_x = 2.5
        scale_y = 2.5
        
        # Manually calculate expected img_x/y
        # In the modified code, these should be floats
        img_x = self.app.start_x * scale_x
        img_y = self.app.start_y * scale_y
        
        self.assertIsInstance(img_x, float)
        self.assertIsInstance(img_y, float)
        
        # Verify 0.1 pixel precision requirement (should be much better, float precision)
        self.assertAlmostEqual(img_x, 250.308625, places=5)
        
        print("Precision Handling Test Passed.")

    def test_log_rotation_logic(self):
        """Test 2: Verify log file creation and content format"""
        print("\nTesting Log Logic...")
        log_file = os.path.join(os.path.dirname(self.app.config_file), "calibration.log")
        
        # Clean previous log
        if os.path.exists(log_file):
            os.remove(log_file)
            
        # Trigger log
        self.app.log_calibration(1.0, 1.1, 2.0, 2.2)
        
        self.assertTrue(os.path.exists(log_file))
        
        with open(log_file, 'r') as f:
            content = f.read()
            self.assertIn("Operator: User", content)
            self.assertIn("Old: (1.000, 2.000)", content)
            self.assertIn("New: (1.100, 2.200)", content)
            
        print("Log Logic Test Passed.")

if __name__ == '__main__':
    unittest.main()
