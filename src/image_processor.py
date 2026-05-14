import cv2
import numpy as np

class ImageProcessor:
    def __init__(self, image_path=None, image_data=None):
        self.image = None
        self.original_image = None
        if image_path:
            self.load_image(image_path)
        elif image_data is not None:
            self.load_from_data(image_data)

    def load_image(self, path):
        """Load image from path."""
        self.image = cv2.imread(path)
        if self.image is None:
            raise ValueError(f"Could not load image from {path}")
            
        # Check and enhance DPI (Resolution) if needed
        self.image = self.enhance_resolution_if_needed(self.image)
        
        self.original_image = self.image.copy()
        return self.image

    def load_from_data(self, img_array):
        """Load image from numpy array (OpenCV format)."""
        self.image = img_array
        
        # Check and enhance DPI (Resolution) if needed
        self.image = self.enhance_resolution_if_needed(self.image)
        
        self.original_image = self.image.copy()
        return self.image

    def enhance_resolution_if_needed(self, img):
        """
        Check if image resolution is too low for precise extraction.
        If min dimension < 2000px, upscale using Super-Resolution or high-quality interpolation.
        Target: Min dimension >= 2000px or 2x upscale.
        """
        if img is None: return None
        
        h, w = img.shape[:2]
        min_dim = min(h, w)
        target_min = 2000
        
        if min_dim < target_min:
            scale = target_min / min_dim
            # Limit max scale to avoid excessive memory usage (e.g., max 4x)
            scale = min(scale, 4.0)
            
            if scale > 1.0:
                print(f"Upscaling image by factor {scale:.2f} (Original: {w}x{h})")
                new_w = int(w * scale)
                new_h = int(h * scale)
                
                # Use Lanczos for high quality down/upscaling, or Cubic for general
                # For pure upscaling, Cubic or Lanczos4 is good.
                # OpenCV INTER_LANCZOS4 is generally best for quality.
                img_upscaled = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)
                
                # Optional: Apply sharpening after upscale to define edges
                # Gaussian blur based unsharp masking
                gaussian = cv2.GaussianBlur(img_upscaled, (0, 0), 2.0)
                img_upscaled = cv2.addWeighted(img_upscaled, 1.5, gaussian, -0.5, 0, img_upscaled)
                
                return img_upscaled
                
        return img


    def preprocess(self):
        """Apply basic preprocessing: denoise, enhance contrast."""
        if self.image is None:
            return None
        
        # Denoise
        self.image = cv2.fastNlMeansDenoisingColored(self.image, None, 10, 10, 7, 21)
        
        # Enhance contrast (optional, maybe histogram equalization if needed)
        # For now, just return the denoised image
        return self.image

    def get_grayscale(self):
        """Convert to grayscale."""
        if self.image is None:
            return None
        return cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)

    def get_edges(self):
        """Get edges using Canny."""
        gray = self.get_grayscale()
        return cv2.Canny(gray, 50, 150)

    def detect_lines(self):
        """Detect lines using Hough Transform (for axis alignment)."""
        edges = self.get_edges()
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=100, minLineLength=100, maxLineGap=10)
        return lines
