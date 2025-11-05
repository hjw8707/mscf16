#!/usr/bin/env python3
"""
MSCF-16 GUI Simple Test

Simple test to verify PyQt5 is working correctly
"""

import sys
import os

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QPushButton
    from PyQt5.QtCore import Qt

    def test_gui():
        app = QApplication(sys.argv)

        # Simple test window
        window = QWidget()
        window.setWindowTitle('MSCF-16 GUI Test')
        window.setGeometry(100, 100, 300, 200)

        layout = QVBoxLayout()

        label = QLabel('MSCF-16 GUI is working correctly!')
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)

        button = QPushButton('Close')
        button.clicked.connect(window.close)
        layout.addWidget(button)

        window.setLayout(layout)
        window.show()

        print("GUI test window is open. Click the close button or close the window.")
        return app.exec_()

    if __name__ == "__main__":
        print("Starting PyQt5 GUI test...")
        sys.exit(test_gui())

except ImportError as e:
    print(f"Failed to import PyQt5: {e}")
    print("Please install PyQt5 with:")
    print("pip install PyQt5")
    sys.exit(1)
except Exception as e:
    print(f"Error occurred during GUI test: {e}")
    sys.exit(1)
