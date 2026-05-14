import unittest
import numpy as np
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from curve_fitter import CurveFitter

class TestCurveFitter(unittest.TestCase):
    def setUp(self):
        self.fitter = CurveFitter()

    def test_linear_fit(self):
        # y = 2x + 1
        x = np.array([0, 1, 2, 3, 4])
        y = np.array([1, 3, 5, 7, 9])
        
        res = self.fitter.fit_data(x, y, 'Linear')
        
        self.assertAlmostEqual(res['params'][0], 2.0, places=4) # Slope
        self.assertAlmostEqual(res['params'][1], 1.0, places=4) # Intercept
        self.assertAlmostEqual(res['r_squared'], 1.0, places=4)

    def test_polynomial_fit(self):
        # y = x^2
        x = np.array([-2, -1, 0, 1, 2])
        y = np.array([4, 1, 0, 1, 4])
        
        res = self.fitter.fit_data(x, y, 'Polynomial', order=2)
        
        # params: [1, 0, 0] approx
        self.assertAlmostEqual(res['params'][0], 1.0, places=4)
        self.assertAlmostEqual(res['r_squared'], 1.0, places=4)

    def test_exponential_fit(self):
        # y = 2 * e^(0.5x)
        x = np.array([0, 1, 2, 3])
        y = 2 * np.exp(0.5 * x)
        
        res = self.fitter.fit_data(x, y, 'Exponential')
        
        # a=2, b=0.5
        self.assertAlmostEqual(res['params'][0], 2.0, places=2)
        self.assertAlmostEqual(res['params'][1], 0.5, places=2)

    def test_logarithmic_fit(self):
        # y = 1 + 2 * ln(x)
        x = np.array([1, 2.718, 7.389])
        y = np.array([1, 3, 5])
        
        res = self.fitter.fit_data(x, y, 'Logarithmic')
        
        # a=1, b=2
        self.assertAlmostEqual(res['params'][0], 1.0, places=2)
        self.assertAlmostEqual(res['params'][1], 2.0, places=2)

if __name__ == '__main__':
    unittest.main()
