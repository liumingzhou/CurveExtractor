import sys
import importlib

packages = [
    'cv2',
    'numpy',
    'pandas',
    'PIL',
    'scipy',
    'openpyxl',
    'matplotlib',
    'pytesseract'
]

missing = []
for pkg in packages:
    try:
        importlib.import_module(pkg)
        print(f"Found {pkg}")
    except ImportError:
        missing.append(pkg)
        print(f"Missing {pkg}")

if missing:
    print("Some packages are missing. Please install them.")
    sys.exit(1)
else:
    print("All packages found.")
