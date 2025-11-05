#!/usr/bin/env python3
"""
MHV-4 GUI Application Launcher
"""

import sys
import os

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    # Import modules directly
    from mhv4_gui import main

    if __name__ == "__main__":
        print("Starting MHV-4 GUI application...")
        if len(sys.argv) > 1:
            print(f"Device port: {sys.argv[1]}")
        main()

except ImportError as e:
    print(f"Import error occurred: {e}")
    print("\nPlease check if required packages are installed:")
    print("  pip install pyserial PyQt5")
    sys.exit(1)
except Exception as e:
    print(f"Error occurred while running the application: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

