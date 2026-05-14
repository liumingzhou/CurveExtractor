import cv2
import numpy as np
import pytesseract

class CoordinateSystem:
    def __init__(self, image):
        self.image = image
        self.plot_area = None # (x, y, w, h)
        self.x_axis_type = 'log' # default
        self.y_axis_type = 'log' # default
        self.x_range = (0.1, 100000) # default min, max
        self.y_range = (0.01, 1000) # default min, max
        
        # Custom reference points [(pixel_val, data_val), ...]
        self.refs_x = []
        self.refs_y = []

    def add_reference_point(self, axis, pixel_val, data_val):
        """Add a manual calibration point."""
        if axis == 'x':
            # Remove existing point if close pixel
            self.refs_x = [p for p in self.refs_x if abs(p[0] - pixel_val) > 5]
            self.refs_x.append((pixel_val, data_val))
            self.refs_x.sort(key=lambda x: x[0])
        elif axis == 'y':
            self.refs_y = [p for p in self.refs_y if abs(p[0] - pixel_val) > 5]
            self.refs_y.append((pixel_val, data_val))
            self.refs_y.sort(key=lambda x: x[0])

    def reset_references(self):
        self.refs_x = []
        self.refs_y = []

    def pixel_to_data(self, px, py):
        """
        Convert pixel coordinates (px, py) to data coordinates (dx, dy).
        Uses reference points if available, otherwise falls back to plot_area.
        """
        if not self.plot_area:
            return None
        
        x0, y0, w, h = self.plot_area
        
        # --- X Mapping ---
        dx = self._map_coordinate(px, self.refs_x, (x0, x0+w), self.x_range, self.x_axis_type)
        
        # --- Y Mapping ---
        # Note: Pixel Y increases downwards. Graph Y usually increases upwards.
        # If using plot_area default: bottom (y0+h) is min, top (y0) is max.
        # If using refs, we trust the refs.
        dy = self._map_coordinate(py, self.refs_y, (y0+h, y0), self.y_range, self.y_axis_type)
            
        return dx, dy

    def _map_coordinate(self, p, refs, default_p_range, default_d_range, scale_type):
        """
        Generic mapping function.
        p: input pixel value
        refs: list of (pixel, value)
        default_p_range: (p_min, p_max) from plot area (e.g. left, right)
        default_d_range: (d_min, d_max) from settings
        scale_type: 'log' or 'linear'
        """
        # Prepare points for interpolation/extrapolation
        points = []
        
        # Strategy: Piecewise Linear Interpolation (Log-Log or Linear)
        # If we have custom refs, use them to find the enclosing segment.
        
        use_log = (scale_type == 'log')
        
        # 1. Use manual references if available and sufficient (>=2 points)
        if len(refs) >= 2:
            # Sort refs by pixel coordinate (already done in add_reference_point but ensuring safety)
            sorted_refs = sorted(refs, key=lambda x: x[0])
            
            ref_pixels = np.array([r[0] for r in sorted_refs])
            ref_vals = np.array([r[1] for r in sorted_refs])
            
            # Find the segment [p_left, p_right] that contains p
            # np.searchsorted finds indices where elements should be inserted to maintain order.
            idx = np.searchsorted(ref_pixels, p)
            
            if idx == 0:
                # p is before the first ref -> Extrapolate using first segment
                p1, p2 = ref_pixels[0], ref_pixels[1]
                v1, v2 = ref_vals[0], ref_vals[1]
            elif idx >= len(ref_pixels):
                # p is after the last ref -> Extrapolate using last segment
                p1, p2 = ref_pixels[-2], ref_pixels[-1]
                v1, v2 = ref_vals[-2], ref_vals[-1]
            else:
                # p is between ref[idx-1] and ref[idx] -> Interpolate
                p1, p2 = ref_pixels[idx-1], ref_pixels[idx]
                v1, v2 = ref_vals[idx-1], ref_vals[idx]
                
            fit_pixels = np.array([p1, p2])
            fit_vals = np.array([v1, v2])
            
        else:
            # Fallback to default range (Min/Max) + any single ref
            p1, p2 = default_p_range
            d1, d2 = default_d_range
            
            fit_pixels = np.array([p1, p2])
            fit_vals = np.array([d1, d2])
            
            # If 1 ref exists, replace the closest default
            if len(refs) == 1:
                rp, rv = refs[0]
                if abs(rp - p1) > abs(rp - p2):
                    fit_pixels = np.array([p1, rp])
                    fit_vals = np.array([d1, rv])
                else:
                    fit_pixels = np.array([rp, p2])
                    fit_vals = np.array([rv, d2])

        # Perform Mapping (Linear or Log) on the selected segment
        if use_log:
            # log(val) = m * pixel + c
            fit_vals = np.array([v if v > 1e-9 else 1e-9 for v in fit_vals])
            log_vals = np.log10(fit_vals)
            
            # Since we always select 2 points (segment), we can use direct formula
            if fit_pixels[1] == fit_pixels[0]: # Avoid div by zero
                 return 10 ** log_vals[0]
                 
            m = (log_vals[1] - log_vals[0]) / (fit_pixels[1] - fit_pixels[0])
            c = log_vals[0] - m * fit_pixels[0]
                
            val_log = m * p + c
            return 10 ** val_log
        else:
            # val = m * pixel + c
            if fit_pixels[1] == fit_pixels[0]:
                 return fit_vals[0]
                 
            m = (fit_vals[1] - fit_vals[0]) / (fit_pixels[1] - fit_pixels[0])
            c = fit_vals[0] - m * fit_pixels[0]
                
            return m * p + c

    def find_plot_area(self):
        """
        Find the main plot area by looking for the largest rectangular contour.
        """
        gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
        # Threshold to get black lines
        _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
        
        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        max_area = 0
        best_rect = None
        
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            area = w * h
            # Filter small areas
            if area > max_area and w > 100 and h > 100:
                max_area = area
                best_rect = (x, y, w, h)
        
        if best_rect:
            self.plot_area = best_rect
            return best_rect
        return None

    def set_calibration(self, x_range, y_range, x_type='log', y_type='log'):
        """
        Manually set calibration if auto-detection fails.
        x_range: (min_val, max_val)
        y_range: (min_val, max_val)
        """
        self.x_range = x_range
        self.y_range = y_range
        self.x_axis_type = x_type
        self.y_axis_type = y_type

    def detect_axes_scales(self):
        """
        Attempt to detect axis scales using OCR.
        """
        if not self.plot_area:
            return None

        x, y, w, h = self.plot_area
        img_h, img_w = self.image.shape[:2]

        # Define ROI for X-axis (below the plot)
        # Take a strip below the plot area
        x_axis_roi_y = min(y + h + 5, img_h)
        x_axis_roi_h = min(50, img_h - x_axis_roi_y) # Height of 50px
        x_roi = self.image[x_axis_roi_y:x_axis_roi_y+x_axis_roi_h, x:x+w]
        
        # Define ROI for Y-axis (left of the plot)
        # Take a strip to the left of the plot area
        y_axis_roi_x = max(0, x - 60) # Width of 60px
        y_axis_roi_w = min(60, x - y_axis_roi_x)
        y_roi = self.image[y:y+h, y_axis_roi_x:y_axis_roi_x+y_axis_roi_w]

        # Perform OCR
        x_text = self._perform_ocr(x_roi)
        y_text = self._perform_ocr(y_roi)
        
        print(f"OCR X: {x_text}")
        print(f"OCR Y: {y_text}")

        # Parse numbers
        x_nums = self._extract_numbers(x_text)
        y_nums = self._extract_numbers(y_text)
        
        if x_nums:
            self.x_range = (min(x_nums), max(x_nums))
            # Heuristic: if range spans orders of magnitude, likely log
            if max(x_nums) / min(x_nums) > 20: 
                self.x_axis_type = 'log'
            else:
                self.x_axis_type = 'linear'
                
        if y_nums:
            self.y_range = (min(y_nums), max(y_nums))
            if max(y_nums) / min(y_nums) > 20:
                self.y_axis_type = 'log'
            else:
                self.y_axis_type = 'linear'
                
        return self.x_range, self.y_range

    def _perform_ocr(self, roi):
        if roi.size == 0:
            return ""
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        # Upscale for better OCR
        gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        # Threshold
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Configure tesseract to look for sparse text
        config = r'--oem 3 --psm 6' 
        return pytesseract.image_to_string(thresh, config=config)

    def _extract_numbers(self, text):
        import re
        # Look for numbers, including scientific notation like 100, 0.1, 1.5, 1E3
        # Also common OCR errors cleanup could go here
        nums = []
        # Pattern: digits, maybe decimal, maybe scientific E
        # Regex to capture:
        # 1. Scientific notation: 1.23E-4, 10^3 (represented as 10 3 often by OCR)
        # 2. Decimals: 0.01, 100.5
        # 3. Integers: 100
        
        # Pre-process text to fix common OCR issues with powers of 10
        # "10 2" -> "100" (if looks like power)
        # "10°" -> "1" or "10^0"
        
        # Replace common OCR artifacts
        text = text.replace('°', '0').replace('O', '0').replace('o', '0')
        
        tokens = re.findall(r"[-+]?\d*\.\d+E[-+]?\d+|[-+]?\d*\.\d+|[-+]?\d+", text)
        for t in tokens:
            try:
                val = float(t)
                nums.append(val)
            except ValueError:
                pass
        
        return sorted(list(set(nums)))

    def validate_log_scale(self, numbers):
        """
        Validates if the extracted numbers form a valid log scale series.
        Returns confidence score (0-1).
        """
        if len(numbers) < 2:
            return 0.0
            
        # Check for powers of 10
        log_vals = np.log10(numbers)
        diffs = np.diff(log_vals)
        
        # Ideally diffs should be close to integers (1, 2, etc.) for major grid lines
        # or have specific patterns.
        
        # Count how many steps are roughly integer
        valid_steps = np.sum(np.abs(diffs - np.round(diffs)) < 0.1)
        score = valid_steps / len(diffs)
        
        return score
