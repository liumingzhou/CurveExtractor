import cv2
import numpy as np
from adaptive_sampler import AdaptiveSampler
try:
    import pytesseract
except ImportError:
    pytesseract = None

class CurveExtractor:
    def __init__(self, image, plot_area):
        self.image = image
        self.plot_area = plot_area # (x, y, w, h)
        
    def extract_blue_curves(self):
        """
        Extract blue curves using full scan (Legacy).
        Kept for compatibility, but internally redirects to adaptive if needed.
        Currently redirects to adaptive for optimization.
        """
        return self.extract_blue_curves_adaptive()

    def extract_blue_curves_adaptive(self):
        """
        Extract blue curves using adaptive step scanning.
        """
        if not self.plot_area:
            return None, None
            
        x0, y0, w, h = self.plot_area
        roi = self.image[y0:y0+h, x0:x0+w]
        
        # --- Pre-processing: Text Removal (OCR) ---
        # Mask out text regions before color thresholding to avoid picking up black text
        clean_roi = roi.copy()
        if pytesseract:
            try:
                # Configure tesseract to treat image as a single block or sparse text
                custom_config = r'--oem 3 --psm 11' 
                boxes = pytesseract.image_to_data(clean_roi, output_type=pytesseract.Output.DICT, config=custom_config)
                
                n_boxes = len(boxes['level'])
                for i in range(n_boxes):
                    if int(boxes['conf'][i]) > 30: # Filter low confidence
                        (x, y, w_box, h_box) = (boxes['left'][i], boxes['top'][i], boxes['width'][i], boxes['height'][i])
                        # Expand box slightly to cover edges/arrows often associated with text
                        pad = 5
                        cv2.rectangle(clean_roi, (x-pad, y-pad), (x+w_box+pad, y+h_box+pad), (255, 255, 255), -1) # Fill with white (background)
            except Exception as e:
                print(f"OCR Text Removal Failed: {e}")

        # --- Color Thresholding ---
        hsv = cv2.cvtColor(clean_roi, cv2.COLOR_BGR2HSV)
        
        # Default Blue Range
        lower_blue = np.array([90, 50, 50])
        upper_blue = np.array([130, 255, 255])
        
        # Check if we should use "Dark" range instead?
        # If the image is B&W, blue mask will be empty.
        # Let's check if we find anything.
        mask = cv2.inRange(hsv, lower_blue, upper_blue)
        
        if cv2.countNonZero(mask) < 100:
            # Fallback: Detect Dark pixels (Black curves)
            # Low Value, Any Hue/Sat
            lower_black = np.array([0, 0, 0])
            upper_black = np.array([180, 255, 100]) # Value < 100
            mask = cv2.inRange(hsv, lower_black, upper_black)
            print("Switched to Dark Pixel detection")

        # --- Post-processing: Noise/Arrow Removal (Contour Filtering) ---
        mask = self._filter_mask(mask)
        
        height, width = mask.shape
        
        # Sampler
        sampler = AdaptiveSampler(min_step=1, max_step=10, threshold_high=3.0, threshold_low=0.5)
        
        min_curve_points = []
        max_curve_points = []
        
        # 1. Row Scan (Y-axis)
        def get_row_min(y):
            if y >= height: return None
            row = mask[int(y), :]
            indices = np.where(row > 0)[0]
            return indices[0] if len(indices) > 0 else None
            
        def get_row_max(y):
            if y >= height: return None
            row = mask[int(y), :]
            indices = np.where(row > 0)[0]
            return indices[-1] if len(indices) > 0 else None

        # Sample Min X (Left edge)
        row_samples_min = sampler.sample(0, height, get_row_min)
        for y, x in row_samples_min:
            min_curve_points.append((x0 + x, y0 + y))
            
        # Sample Max X (Right edge)
        row_samples_max = sampler.sample(0, height, get_row_max)
        for y, x in row_samples_max:
            max_curve_points.append((x0 + x, y0 + y))
            
        # 2. Column Scan (X-axis)
        def get_col_max(x): # Bottom edge (Max Y)
            if x >= width: return None
            col = mask[:, int(x)]
            indices = np.where(col > 0)[0]
            return indices[-1] if len(indices) > 0 else None
            
        def get_col_min(x): # Top edge (Min Y)
            if x >= width: return None
            col = mask[:, int(x)]
            indices = np.where(col > 0)[0]
            return indices[0] if len(indices) > 0 else None
            
        col_samples_min = sampler.sample(0, width, get_col_max) # Bottom -> Min Curve
        for x, y in col_samples_min:
            min_curve_points.append((x0 + x, y0 + y))
            
        col_samples_max = sampler.sample(0, width, get_col_min) # Top -> Max Curve
        for x, y in col_samples_max:
            max_curve_points.append((x0 + x, y0 + y))
            
        # Deduplicate and Sort
        min_curve_points = sorted(list(set(min_curve_points)), key=lambda p: p[1])
        max_curve_points = sorted(list(set(max_curve_points)), key=lambda p: p[1])
        
        return min_curve_points, max_curve_points

    def _filter_mask(self, mask):
        """
        Remove small noise, text, and arrows using morphological ops and contour analysis.
        """
        # 1. Morphological Open to remove small dots/lines
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        
        # 2. Find Contours
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return mask
            
        # 3. Filter by Arc Length (Keep only long curves)
        valid_contours = []
        for cnt in contours:
            # Calculate length
            length = cv2.arcLength(cnt, False) # Open or closed
            area = cv2.contourArea(cnt)
            
            # Heuristics:
            # - Curves are long (> 100 px)
            # - Text/Arrows are usually small or compact
            if length > 100 or area > 500:
                valid_contours.append(cnt)
                
        # If we have too many valid contours, maybe keep top 5 by length?
        if len(valid_contours) > 5:
            valid_contours = sorted(valid_contours, key=lambda c: cv2.arcLength(c, False), reverse=True)[:5]
            
        # Re-draw mask
        clean_mask = np.zeros_like(mask)
        cv2.drawContours(clean_mask, valid_contours, -1, 255, thickness=cv2.FILLED)
        # Also draw contours as lines to ensure connectivity if FILLED missed thin lines
        cv2.drawContours(clean_mask, valid_contours, -1, 255, thickness=2)
        
        return clean_mask

    def extract_by_color(self, color_lower, color_upper):
        """Generic color extraction."""
        pass
