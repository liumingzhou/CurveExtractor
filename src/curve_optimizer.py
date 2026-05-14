import numpy as np
from scipy.interpolate import CubicSpline, Akima1DInterpolator
from scipy.signal import savgol_filter

class CurveOptimizer:
    """
    Implements advanced curve optimization:
    1. Direct X-smoothing using Savitzky-Golay filter (preserves shape, reduces noise)
    2. Adaptive window sizing based on data density
    3. Strict anchor preservation (Start/End)
    """
    
    def __init__(self):
        pass
        
    def optimize_curve(self, points, iterations=3, window_ratio=0.1):
        """
        Input: List of dicts {'Data_X': float, 'Data_Y': float, ...}
        Output: 
            - optimized_points: List of dicts with optimized X
            - metrics: Dict containing quality report
        """
        if not points or len(points) < 5:
            return points, {}
            
        # Extract arrays
        y_vals = np.array([p['Data_Y'] for p in points])
        x_vals = np.array([p['Data_X'] for p in points])
        
        # Log transform X and Y for processing (TCC curves are log-log usually)
        # Handle zeros/negative
        y_log = np.log10(np.maximum(y_vals, 1e-9))
        x_log = np.log10(np.maximum(x_vals, 1e-9))
        
        # Sort by Y for processing (Must be monotonic for X=f(Y) smoothing)
        sort_idx = np.argsort(y_log)
        y_proc = y_log[sort_idx]
        x_proc = x_log[sort_idx]
        
        # Remove duplicates in Y (interpolation/filtering works better)
        unique_y, unique_idx = np.unique(y_proc, return_index=True)
        y_proc = y_proc[unique_idx]
        x_proc = x_proc[unique_idx]
        
        if len(y_proc) < 5:
            return points, {}

        try:
            # --- Slope-Based Optimization Strategy (Integration Method) ---
            # 1. Resample to uniform grid for consistent slope processing
            num_samples = max(200, len(y_proc) * 2) # Upsample
            y_uniform = np.linspace(y_proc[0], y_proc[-1], num_samples)
            
            # Linear Interpolation to get initial X on uniform grid
            x_uniform = np.interp(y_uniform, y_proc, x_proc)
            
            # 2. Calculate Slopes
            dy = y_uniform[1] - y_uniform[0]
            slopes = np.gradient(x_uniform, dy)
            
            # 3. Iterative Slope Smoothing
            # Filter the slopes, not the positions. This ensures C1 continuity.
            
            # Determine window size based on data density
            # A larger window = smoother curve
            win_len = int(num_samples * window_ratio)
            if win_len % 2 == 0: win_len += 1
            win_len = max(5, win_len)
            
            current_slopes = slopes.copy()
            
            for _ in range(iterations):
                # Apply Savitzky-Golay to Slopes
                current_slopes = savgol_filter(current_slopes, win_len, polyorder=2)
                
                # Optional: Clamp slopes if needed (e.g. max steepness)
                # threshold = np.percentile(np.abs(current_slopes), 99) * 2
                # current_slopes = np.clip(current_slopes, -threshold, threshold)
            
            # 4. Reconstruct Curve (Integration)
            # x[i] = x[0] + sum(slope * dy)
            x_integrated = np.cumsum(current_slopes * dy)
            
            # Adjust start point (cumsum starts at slope[0]*dy, roughly)
            # Actually cumsum is integral.
            # We need to prepend 0 to match size or integrate properly.
            # Simple Euler integration:
            x_reconstructed = np.zeros_like(x_uniform)
            x_reconstructed[0] = x_uniform[0]
            for i in range(1, len(x_uniform)):
                x_reconstructed[i] = x_reconstructed[i-1] + current_slopes[i-1] * dy # or average slope
                
            # 5. Drift Correction (Anchor Preservation)
            # The integrated curve might not end exactly at the original end point.
            # We distribute the error linearly.
            error = x_uniform[-1] - x_reconstructed[-1]
            correction = np.linspace(0, error, num_samples)
            x_final_uniform = x_reconstructed + correction
            
            # 6. Map back to Original Y Points (or keep dense?)
            # User wants "smoothness". Dense points are better.
            # But we should probably return points corresponding to the visualization density.
            # Let's return the DENSE uniform points for high quality export.
            
            x_final = x_final_uniform
            y_final = y_uniform
            
            # --- Calculate Metrics ---
            dx_dy = np.gradient(x_final, y_final)
            d2x_dy2 = np.gradient(dx_dy, y_final)
            d2x_dy2[np.abs(d2x_dy2) < 1e-6] = 1e-6
            curvature_radius = np.abs((1 + dx_dy**2)**1.5 / d2x_dy2)
    
            optimized_points = []
            for i in range(len(y_final)):
                # Transform back from Log
                orig_y = 10**y_final[i]
                orig_x = 10**x_final[i]
                
                point = {
                    'Data_Y': float(orig_y),
                    'Data_X': float(orig_x),
                    'Original_X': float(10**np.interp(y_final[i], y_proc, x_proc)), # Estimated original
                    'Slope': float(dx_dy[i]),
                    'Curvature_Radius': float(curvature_radius[i])
                }
                optimized_points.append(point)
                
            # Report
            report = {
                'method': 'Slope Integration (Iterative)',
                'window': win_len,
                'iterations': iterations,
                'points_generated': len(optimized_points)
            }
            
            return optimized_points, report

        except Exception as e:
            # Fallback to original points on critical failure
            print(f"Optimization Failed: {e}")
            import traceback
            traceback.print_exc()
            return points, {'error': str(e)}
