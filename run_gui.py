#!/usr/bin/env python3
"""
MSCF-16 GUI 런처

MSCF-16 GUI 애플리케이션을 실행하는 간단한 런처 스크립트
"""

import sys
import os

# 현재 디렉토리를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    # 직접 모듈들을 임포트
    from mscf16_gui import main

    if __name__ == "__main__":
        print("MSCF-16 GUI 애플리케이션을 시작합니다...")
        main()

except ImportError as e:
    print(f"필요한 모듈을 가져올 수 없습니다: {e}")
    print("현재 디렉토리:", current_dir)
    print("Python 경로:")
    for path in sys.path:
        print(f"  {path}")
    print("\n다음 명령어로 필요한 패키지를 설치하세요:")
    print("pip install -r requirements.txt")
    sys.exit(1)
except Exception as e:
    print(f"애플리케이션 실행 중 오류가 발생했습니다: {e}")
    sys.exit(1)
