import numpy as np

class AdaptiveSampler:
    """
    Implements an adaptive step size sampling algorithm for curve extraction.
    """
    def __init__(self, min_step=1, max_step=20, threshold_high=5.0, threshold_low=1.0):
        self.min_step = min_step
        self.max_step = max_step
        self.threshold_high = threshold_high # Pixel difference triggering step reduction
        self.threshold_low = threshold_low   # Pixel difference triggering step increase

    def sample(self, start, end, get_value_func):
        """
        Adaptively samples the range [start, end).
        get_value_func: function(index) -> value (or None if no data)
        Returns list of (index, value) tuples.
        """
        points = []
        current = start
        step = self.min_step # Start cautious
        
        # Initial point
        val = get_value_func(current)
        if val is not None:
            points.append((current, val))
        
        while current < end:
            # Propose next point
            next_pos = int(current + step)
            if next_pos >= end:
                next_pos = end - 1
                if next_pos <= current:
                    break
            
            val = get_value_func(next_pos)
            
            if val is None:
                # Gap encountered.
                # Strategy: Reduce step to min to find re-entry, or skip if big gap?
                # For curve extraction, we might have noise.
                # Let's reduce step to minimize gap size, but if min step, just move on.
                if step > self.min_step:
                    step = max(self.min_step, step / 2)
                    continue # Retry with smaller step from SAME current
                else:
                    # Move forward blindly
                    current += self.min_step
                    continue
            
            if not points:
                points.append((next_pos, val))
                current = next_pos
                continue
                
            # Analyze change
            prev_pos, prev_val = points[-1]
            
            # Change rate: Absolute difference / Step size
            # Or just absolute difference? 
            # If curve is steep, difference is high. We want more points there.
            # So if Diff > Threshold, we want smaller step.
            
            diff = abs(val - prev_val)
            
            if diff > self.threshold_high:
                # Change too drastic
                if step > self.min_step:
                    # Reject this point, reduce step and retry
                    step = max(self.min_step, step / 2)
                    # Don't advance current
                else:
                    # Step is already min, must accept
                    points.append((next_pos, val))
                    current = next_pos
            
            elif diff < self.threshold_low:
                # Very flat
                points.append((next_pos, val))
                current = next_pos
                # Increase step for next iteration
                # Allow step to grow faster if very flat
                # Increased to 5.0x as requested for smoother transitions in flat areas
                step = min(self.max_step, step * 5.0)
                
            else:
                # Normal range
                points.append((next_pos, val))
                current = next_pos
                # Keep step or slowly relax?
                # Slightly increase step to be optimistic
                step = min(self.max_step, step * 1.1)
        
        return points
