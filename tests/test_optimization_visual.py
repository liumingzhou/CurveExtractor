import unittest
import numpy as np
import os
import sys
import matplotlib.pyplot as plt

# Add src to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))
from curve_optimizer import CurveOptimizer

class TestOptimizationVisual(unittest.TestCase):
    def test_optimization_quality(self):
        print("\nTesting Optimization Quality...")
        
        # 1. Generate Synthetic TCC Curve (Inverse Time)
        # t = k / (I^p - 1)
        # Let's use simple log-log linear-ish segment + curvature
        # Log(t) = -p * Log(I) + C
        
        # Generate 50 points (sparse)
        i_current = np.logspace(0, 4, 50) # 1A to 10000A
        t_time = 100 / (i_current**0.5) # Simple inverse square root
        
        # Add Noise (Jitter in Log Space)
        noise_level = 0.05
        t_noisy = t_time * (1 + np.random.normal(0, noise_level, len(t_time)))
        
        # Create input format
        points = []
        for x, y in zip(i_current, t_noisy):
            points.append({'Data_X': x, 'Data_Y': y})
            
        # 2. Optimize
        optimizer = CurveOptimizer()
        
        # Level 5 (Moderate)
        opt_points, report = optimizer.optimize_curve(points, iterations=2, window_ratio=0.1)
        
        # Extract results
        x_opt = [p['Data_X'] for p in opt_points]
        y_opt = [p['Data_Y'] for p in opt_points]
        
        # 3. Calculate Metrics (Smoothness)
        # Smoothness ~ 1 / Variance of 2nd derivative of Log-Log curve
        def calc_roughness(x, y):
            lx = np.log10(x)
            ly = np.log10(y)
            # Sort by Y (as optimizer does)
            idx = np.argsort(ly)
            lx = lx[idx]
            ly = ly[idx]
            
            d1 = np.gradient(lx, ly)
            d2 = np.gradient(d1, ly)
            return np.std(d2)
            
        rough_orig = calc_roughness(i_current, t_noisy)
        rough_opt = calc_roughness(x_opt, y_opt)
        
        print(f"Original Roughness (Std of 2nd Deriv): {rough_orig:.4f}")
        print(f"Optimized Roughness (Std of 2nd Deriv): {rough_opt:.4f}")
        print(f"Improvement Factor: {rough_orig/rough_opt:.2f}x")
        print(f"Report: {report}")
        
        # 4. Plot
        plt.figure(figsize=(10, 6))
        plt.loglog(i_current, t_noisy, 'r.', alpha=0.5, label='Noisy Input')
        plt.loglog(i_current, t_time, 'k--', alpha=0.5, label='True Curve')
        plt.loglog(x_opt, y_opt, 'b-', linewidth=2, label='Optimized Output')
        plt.grid(True, which="both", ls="-")
        plt.xlabel('Current (A)')
        plt.ylabel('Time (s)')
        plt.title(f'Curve Optimization Test\nRoughness: {rough_orig:.4f} -> {rough_opt:.4f}')
        plt.legend()
        
        output_file = os.path.join(os.path.dirname(__file__), 'optimization_test_result.png')
        plt.savefig(output_file)
        print(f"Comparison plot saved to: {output_file}")
        
        self.assertLess(rough_opt, rough_orig, "Optimization should improve smoothness")

if __name__ == '__main__':
    unittest.main()
