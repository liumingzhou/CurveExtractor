import cv2
import numpy as np
import pandas as pd
import os
import sys

# Mock classes to reproduce the logic without full GUI
class MockCoordinateSystem:
    def __init__(self, x_range, y_range, rect):
        self.x_range = x_range
        self.y_range = y_range
        self.plot_area = rect
        self.x_axis_type = 'log'
        self.y_axis_type = 'log'
        self.refs_x = []
        self.refs_y = []

    def pixel_to_data(self, px, py):
        x0, y0, w, h = self.plot_area
        
        # Normalize
        norm_x = (px - x0) / w
        norm_y = (y0 + h - py) / h
        
        # Log mapping
        lx1, lx2 = np.log10(self.x_range[0]), np.log10(self.x_range[1])
        ly1, ly2 = np.log10(self.y_range[0]), np.log10(self.y_range[1])
        
        dx = 10**(lx1 + norm_x * (lx2 - lx1))
        dy = 10**(ly1 + norm_y * (ly2 - ly1))
        
        return dx, dy

def reproduce_extraction():
    # 1. Load Image (Synthesize a test image if actual one not available)
    # Since I cannot see the user's image, I will create a synthetic TCC-like image
    # Black axes, Blue band
    
    W, H = 800, 600
    img = np.ones((H, W, 3), dtype=np.uint8) * 255
    
    # Draw Plot Area
    x0, y0, w, h = 50, 50, 700, 500
    cv2.rectangle(img, (x0, y0), (x0+w, y0+h), (0,0,0), 2)
    
    # Draw a blue curve (Band)
    # Let's simulate a curve going from top-left to bottom-right with a vertical drop
    points_min = []
    points_max = []
    
    # Part 1: Diagonal
    for i in range(100):
        px = x0 + 10 + i*2
        py = y0 + 10 + i*2
        points_min.append((px, py))
        points_max.append((px+20, py))
        
    # Part 2: Vertical drop
    last_x_min = points_min[-1][0]
    last_y = points_min[-1][1]
    for i in range(200):
        py = last_y + i
        points_min.append((last_x_min, py))
        points_max.append((last_x_min+20, py))
        
    # Part 3: Horizontal
    last_x_min = points_min[-1][0]
    last_y = points_min[-1][1]
    for i in range(100):
        px = last_x_min + i
        points_min.append((px, last_y))
        points_max.append((px+20, last_y))

    # Draw on image
    # Use fillPoly to make it a solid band
    pts = np.array(points_min + points_max[::-1], np.int32)
    pts = pts.reshape((-1, 1, 2))
    cv2.fillPoly(img, [pts], (255, 200, 100)) # BGR: Light Blue
    
    # Save for debug
    cv2.imwrite("test_repro.png", img)
    
    # 2. Extract
    # Import the actual extractor logic
    sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
    from curve_extractor import CurveExtractor
    
    extractor = CurveExtractor(img, (x0, y0, w, h))
    min_pixels, max_pixels = extractor.extract_blue_curves()
    
    print(f"Extracted Pixels: Min={len(min_pixels)}, Max={len(max_pixels)}")
    
    # 3. Process to Data
    coord_sys = MockCoordinateSystem((0.1, 1000), (0.01, 1000), (x0, y0, w, h))
    
    def process(pixels, name):
        points = []
        for px, py in pixels:
            dx, dy = coord_sys.pixel_to_data(px, py)
            points.append({'Pixel_X': px, 'Pixel_Y': py, 'Data_X': dx, 'Data_Y': dy})
            
        # Density Filter (New Logic)
        points.sort(key=lambda p: p['Data_Y'], reverse=True)
        filtered = []
        if points:
            filtered.append(points[0])
            for i in range(1, len(points)):
                curr = points[i]
                prev = filtered[-1]
                dist = np.sqrt((curr['Pixel_X'] - prev['Pixel_X'])**2 + (curr['Pixel_Y'] - prev['Pixel_Y'])**2)
                if dist >= 2.0:
                    filtered.append(curr)
        return filtered

    min_data = process(min_pixels, 'Min')
    max_data = process(max_pixels, 'Max')
    
    print(f"Processed Data: Min={len(min_data)}, Max={len(max_data)}")
    
    # 4. Assertions
    assert len(min_data) >= 100, f"Min Curve points {len(min_data)} < 100"
    assert len(max_data) >= 100, f"Max Curve points {len(max_data)} < 100"
    
    # Check Monotonicity (roughly) or Range
    y_vals = [p['Data_Y'] for p in min_data]
    print(f"Y Range: {min(y_vals):.4f} - {max(y_vals):.4f}")
    
    # 5. Export
    df = pd.DataFrame(min_data)
    df.to_csv("repro_output.csv", index=False)
    print("Exported to repro_output.csv")

if __name__ == "__main__":
    reproduce_extraction()
