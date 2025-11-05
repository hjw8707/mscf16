#!/usr/bin/env python3
"""
MHV-4 GUI Application Launcher
"""

import sys
import os

# 현재 디렉토리를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    # 직접 모듈들을 임포트
    from mhv4_gui import main

    if __name__ == "__main__":
        print("MHV-4 GUI 애플리케이션을 시작합니다...")
        if len(sys.argv) > 1:
            print(f"디바이스 포트: {sys.argv[1]}")
        main()

except ImportError as e:
    print(f"임포트 오류가 발생했습니다: {e}")
    print("\n필요한 패키지가 설치되어 있는지 확인하세요:")
    print("  pip install pyserial PyQt5")
    sys.exit(1)
except Exception as e:
    print(f"애플리케이션 실행 중 오류가 발생했습니다: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

