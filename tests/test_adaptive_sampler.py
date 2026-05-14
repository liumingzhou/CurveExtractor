import unittest
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from adaptive_sampler import AdaptiveSampler

class TestAdaptiveSampler(unittest.TestCase):
    def setUp(self):
        self.sampler = AdaptiveSampler(min_step=1, max_step=10, threshold_high=5.0, threshold_low=1.0)

    def test_linear_flat(self):
        # f(x) = 10 (Flat line)
        def func(x): return 10
        
        points = self.sampler.sample(0, 100, func)
        # Should take max steps (10) mostly
        # Start at 0 -> 1 (diff=0) -> step grows to 10 -> 11, 21, 31...
        # 0, 1, 2, 4, 7, 11, 21...
        self.assertTrue(len(points) < 20, f"Too many points for flat line: {len(points)}")
        self.assertEqual(points[0][0], 0)
        
    def test_linear_steep(self):
        # f(x) = 10 * x (Steep line)
        def func(x): return 10 * x
        
        points = self.sampler.sample(0, 50, func)
        # Change is 10 per step=1. Threshold high is 5.
        # So diff=10 > 5 -> reduce step.
        # Min step is 1. So it should sample every point.
        self.assertTrue(len(points) >= 49, f"Should sample densely for steep line: {len(points)}")
        
    def test_step_function(self):
        # f(x) = 0 if x < 50 else 100
        def func(x): return 0 if x < 50 else 100
        
        points = self.sampler.sample(0, 100, func)
        
        # Should be sparse before 50, dense around 50, sparse after
        # Check if we captured the jump
        indices = [p[0] for p in points]
        
        # We expect points close to 50
        has_near_50 = any(48 <= i <= 52 for i in indices)
        self.assertTrue(has_near_50, "Should sample near the step change")
        
    def test_gaps(self):
        # f(x) = x if x < 10 or x > 20 else None
        def func(x): return x if (x < 10 or x > 20) else None
        
        points = self.sampler.sample(0, 30, func)
        # Should handle None gracefully
        indices = [p[0] for p in points]
        # Should have points in [0,10] and [21,30]
        # Should skip [10,20]
        in_gap = any(10 <= i <= 20 for i in indices)
        self.assertFalse(in_gap, "Should not return None values")
        
if __name__ == '__main__':
    unittest.main()
