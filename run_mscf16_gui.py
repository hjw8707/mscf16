#!/usr/bin/env python3
"""
MSCF-16 GUI Launcher

Simple launcher script for MSCF-16 GUI application
"""

import sys
import os

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    # Import modules directly
    from mscf16_gui import main

    if __name__ == "__main__":
        print("Starting MSCF-16 GUI application...")
        main()

except ImportError as e:
    print(f"Failed to import required modules: {e}")
    print("Current directory:", current_dir)
    print("Python path:")
    for path in sys.path:
        print(f"  {path}")
    print("\nPlease install required packages with:")
    print("pip install -r requirements.txt")
    sys.exit(1)
except Exception as e:
    print(f"Error occurred while running the application: {e}")
    sys.exit(1)
