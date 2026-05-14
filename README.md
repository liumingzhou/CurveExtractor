# Scientific Curve Extractor System

## Overview
This system is designed to automatically identify and extract data curves from scientific charts, specifically supporting logarithmic coordinate systems. It provides a graphical interface for users to load images, calibrate axes, and export extracted data to CSV or Excel.

## Features
1.  **Image Preprocessing**: Denoising and basic enhancement.
2.  **Coordinate System Recognition**: Automatic detection of plot area and support for Log-Log, Semi-Log, and Linear scales.
3.  **Curve Extraction**: Color-based extraction of data curves (e.g., blue trip curves).
4.  **Data Mapping**: High-precision mapping from pixel coordinates to data values.
5.  **Export**: Save results to CSV or Excel formats.

## Installation

### Prerequisites
- Python 3.8+
- Tesseract OCR (Optional, for automatic label reading)
  - Windows: [Download Installer](https://github.com/UB-Mannheim/tesseract/wiki)
  - Add Tesseract to your system PATH.

### Setup
1.  Clone or download this repository.
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

1.  **Run the Application**:
    ```bash
    python main.py
    ```

2.  **Load Image**:
    - Click "Load Image" and select your chart file (PNG, JPG, TIFF).
    - Alternatively, copy an image to your clipboard and click **"Paste Clipboard"**.
    - The system will attempt to auto-detect the plot area (red box).

3.  **Calibrate Axes**:
    - Verify the X and Y axis ranges (Min, Max) in the top control panel.
    - Select "Log" or "Linear" for each axis type.
    - *Note*: Ensure the red box accurately bounds the data area (inner grid). If not, re-check the detection (future version will support manual box adjustment).

4.  **Extract Data**:
    - Click "Extract Data".
    - The system will identify the blue curve(s) and sample points.
    - Extracted points will be visualized as green (upper) and yellow (lower) dots.

5.  **Curve Fitting & Export**:
    - **Select Model**: Choose from Linear, Polynomial, Exponential, Logarithmic, or Power.
    - **Order**: Set the polynomial order (if applicable).
    - **Confidence**: Set the confidence interval (default 0.95).
    - **Plot**: Check to generate PNG/SVG plots of the fit.
    - Click **"Export Result"** to save:
        - `Raw Data`: The extracted points.
        - `Fit Summary`: Equations, R², Parameters.
        - `Fit Details`: Predicted values and residuals.
        - `*_fit.png/svg`: High-resolution plots.

## Algorithm Details

### 1. Coordinate System Detection
The system uses OpenCV to find the largest rectangular contour in the image, which typically corresponds to the axes box. It then maps pixel coordinates $(p_x, p_y)$ to data coordinates $(d_x, d_y)$ using the following logarithmic transformation (for log scale):

$$ d_x = 10^{\log(X_{min}) + \frac{p_x - x_0}{width} \times (\log(X_{max}) - \log(X_{min}))} $$

### 2. Curve Extraction
The system converts the image to HSV color space and applies a threshold to isolate the target curve color (default: Blue). It then scans each column of pixels to find the upper and lower bounds of the curve, handling line thickness and overlaps.

### 3. Curve Fitting
The system uses `scipy.optimize` to fit the extracted data to the selected mathematical model. It calculates the coefficient of determination ($R^2$) and performs residual analysis to evaluate the fit quality.

## Project Structure
- `src/image_processor.py`: Image loading and preprocessing.
- `src/coordinate_system.py`: Axis detection and coordinate mapping.
- `src/curve_extractor.py`: Curve recognition logic.
- `src/curve_fitter.py`: Curve fitting and plotting module.
- `src/gui.py`: Tkinter-based user interface.
- `main.py`: Entry point.
- `tests/`: Unit and integration tests.
