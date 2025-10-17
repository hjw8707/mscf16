#!/usr/bin/env python3
"""
MSCF-16 GUI 간단 테스트

PyQt5가 정상적으로 작동하는지 확인하는 간단한 테스트
"""

import sys
import os

# 현재 디렉토리를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QPushButton
    from PyQt5.QtCore import Qt

    def test_gui():
        app = QApplication(sys.argv)

        # 간단한 테스트 윈도우
        window = QWidget()
        window.setWindowTitle('MSCF-16 GUI 테스트')
        window.setGeometry(100, 100, 300, 200)

        layout = QVBoxLayout()

        label = QLabel('MSCF-16 GUI가 정상적으로 작동합니다!')
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)

        button = QPushButton('닫기')
        button.clicked.connect(window.close)
        layout.addWidget(button)

        window.setLayout(layout)
        window.show()

        print("GUI 테스트 창이 열렸습니다. 닫기 버튼을 클릭하거나 창을 닫으세요.")
        return app.exec_()

    if __name__ == "__main__":
        print("PyQt5 GUI 테스트를 시작합니다...")
        sys.exit(test_gui())

except ImportError as e:
    print(f"PyQt5를 가져올 수 없습니다: {e}")
    print("다음 명령어로 PyQt5를 설치하세요:")
    print("pip install PyQt5")
    sys.exit(1)
except Exception as e:
    print(f"GUI 테스트 중 오류가 발생했습니다: {e}")
    sys.exit(1)
