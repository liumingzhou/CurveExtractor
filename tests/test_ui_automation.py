import unittest
import tkinter as tk
import sys
import os
import json
import threading
import time
import inspect

# Add src to path
src_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src')
sys.path.append(src_path)
from gui import CurveExtractorApp

class TestCurveExtractorUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = tk.Tk()
        cls.app = CurveExtractorApp(cls.root)
        
    @classmethod
    def tearDownClass(cls):
        cls.root.destroy()
        
    def test_log_scale_toggle_persistence(self):
        """Test 3: Log scale button state changes and persistence"""
        print("\nTesting Log Scale Toggle Persistence...")
        
        # Set X and Y log independently
        self.app.x_log_var.set(True)
        self.app.y_log_var.set(False)
        self.app.on_axis_log_changed()
        self.assertTrue(self.app.x_log_var.get())
        self.assertFalse(self.app.y_log_var.get())
        
        # Toggle both ON
        self.app.x_log_var.set(True)
        self.app.y_log_var.set(True)
        self.app.on_axis_log_changed()
        self.assertTrue(self.app.x_log_var.get())
        self.assertTrue(self.app.y_log_var.get())
        
        # Save settings
        self.app.save_settings()
        
        # Simulate restart (Load settings)
        # Reset vars first
        self.app.x_log_var.set(False)
        self.app.y_log_var.set(False)
        self.app.load_settings()
        
        # Verify persistence
        self.assertTrue(self.app.x_log_var.get(), "X log var should be True after reload")
        self.assertTrue(self.app.y_log_var.get(), "Y log var should be True after reload")
        
        print("Log Scale Persistence Test Passed.")

    def test_calibration_dialog_text(self):
        """Test 2: Verify calibration dialog text content (Static analysis)"""
        print("\nVerifying Calibration Dialog Logic...")
        # Since we cannot visually verify the dialog without blocking, 
        # we check the code logic in handle_calibration_click via inspection.
        
        source = inspect.getsource(self.app.handle_calibration_click)
        
        self.assertIn('tk.Toplevel(self.root)', source, "Should use Toplevel for custom dialog")
        
        # New checks for Split Interface
        self.assertIn('text="X轴：请输入X轴坐标值"', source, "Should contain X-axis specific prompt")
        self.assertIn('text="Y轴：请输入Y轴坐标值"', source, "Should contain Y-axis specific prompt")
        
        # Check conditional logic structure
        self.assertIn("if axis == 'x':", source, "Should contain axis conditional logic")
        
        print("Calibration Dialog Text Check Passed.")

if __name__ == '__main__':
    unittest.main()
