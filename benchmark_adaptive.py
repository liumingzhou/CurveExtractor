import time
import numpy as np
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from adaptive_sampler import AdaptiveSampler

def benchmark():
    print("# Adaptive Sampler Performance Benchmark")
    print("| Scenario | Range | Full Scan Points | Adaptive Points | Reduction (%) | Time (ms) |")
    print("|---|---|---|---|---|---|")
    
    scenarios = [
        ("Flat (y=10)", lambda x: 10, 1000),
        ("Slope (y=x)", lambda x: x, 1000),
        ("Sine (y=sin(x/10))", lambda x: np.sin(x/10)*10, 1000),
        ("Step (y=0|100)", lambda x: 0 if x < 500 else 100, 1000)
    ]
    
    sampler = AdaptiveSampler(min_step=1, max_step=20, threshold_high=2.0, threshold_low=0.5)
    
    for name, func, size in scenarios:
        # Full Scan
        start_t = time.perf_counter()
        full_points = []
        for i in range(size):
            full_points.append(func(i))
        full_time = (time.perf_counter() - start_t) * 1000
        
        # Adaptive
        start_t = time.perf_counter()
        adaptive_points = sampler.sample(0, size, func)
        adp_time = (time.perf_counter() - start_t) * 1000
        
        count_full = size
        count_adp = len(adaptive_points)
        reduction = (1 - count_adp/count_full) * 100
        
        print(f"| {name} | 0-{size} | {count_full} | {count_adp} | {reduction:.1f}% | {adp_time:.2f} |")

if __name__ == "__main__":
    benchmark()
