# MSCF-16 NIM Device Controller

MSCF-16 NIM 장치를 제어하는 Python 라이브러리 및 PyQt5 GUI 애플리케이션

## 주요 기능

- **시리얼 통신**: MSCF-16 장치와의 완전한 시리얼 통신 지원
- **GUI 인터페이스**: 사용자 친화적인 PyQt5 기반 GUI
- **완전한 명령어 지원**: 모든 MSCF-16 명령어를 파이썬 메서드로 구현
- **에러 처리**: 포괄적인 파라미터 검증 및 에러 처리
- **실시간 상태 표시**: 연결 상태, 로그, 장치 정보 표시

## 설치

```bash
pip install -r requirements.txt
```

## GUI 애플리케이션 사용법

### 1. GUI 실행

```bash
python run_gui.py
```

### 2. GUI 기능

#### 연결 설정

- 사용 가능한 시리얼 포트 자동 감지
- Baud rate 선택 (9600, 19200, 28400, 57600, 115200)
- 연결 상태 실시간 표시

#### 채널별 제어

- 개별 채널 (1-16) 또는 공통 모드 설정
- Threshold 값 설정 (0-255)
- PZ 값 설정 (0-255)
- Monitor 채널 설정
- 자동 PZ 설정

#### 그룹별 제어

- 그룹별 (1-4) 또는 공통 모드 설정
- Shaping Time 설정 (0-15)
- Gain 설정 (0-15)

#### 고급 제어

- Coincidence Window 설정
- Shaper/Threshold Offset 설정
- 모드 설정 (Single Channel, ECL Delay, BLR Mode)
- Multiplicity Borders 설정
- RC 모드 제어

#### 상태 및 로그

- 펌웨어 버전 확인
- 현재 설정 표시
- 실시간 로그 표시

## 프로그래밍 API 사용법

### 기본 사용법

```python
from mscf16 import MSCF16Controller

# 컨트롤러 초기화
controller = MSCF16Controller(port='COM3', baudrate=9600)

# 연결 및 설정
controller.connect()
controller.set_threshold(1, 128)  # 채널 1에 threshold 128 설정
controller.set_pz_value(1, 100)    # 채널 1에 pz 값 100 설정
version = controller.get_version() # 펌웨어 버전 확인
controller.disconnect()
```

### Context Manager 사용

```python
with MSCF16Controller(port='COM3') as controller:
    controller.set_threshold(1, 128)
    controller.set_pz_value(1, 100)
    # 자동으로 연결 해제됨
```

### 고급 사용법

```python
# 공통 모드 설정
controller.set_threshold(17, 150)  # 모든 채널에 공통 threshold
controller.set_pz_value(17, 120)  # 모든 채널에 공통 pz

# 그룹 공통 설정
controller.set_shaping_time(5, 10)  # 모든 그룹에 공통 shaping time
controller.set_gain(5, 8)          # 모든 그룹에 공통 gain

# 모드 설정
controller.set_single_channel_mode(False)
controller.set_ecl_delay(True)
controller.set_blr_mode(True)

# Multiplicity 설정
controller.set_multiplicity_borders(5, 2)
```

## 테스트 및 예제

### 테스트 실행

```bash
python test_mscf16.py COM3  # Windows
python test_mscf16.py /dev/ttyUSB0  # Linux
```

### 사용 예제 확인

```bash
python example_usage.py
```

## 시스템 요구사항

- Python 3.6+
- pyserial >= 3.5
- PyQt5 >= 5.15.0

## 지원되는 플랫폼

- Windows (COM 포트)
- Linux (/dev/ttyUSB*, /dev/ttyACM*)
- macOS (/dev/cu.usbserial-*, /dev/cu.usbmodem-*)

## 문제 해결

### 연결 문제

1. 장치가 올바르게 연결되어 있는지 확인
2. 올바른 시리얼 포트를 선택했는지 확인
3. 다른 프로그램에서 포트를 사용하고 있지 않은지 확인
4. USB 드라이버가 올바르게 설치되어 있는지 확인

### GUI 실행 문제

1. PyQt5가 올바르게 설치되어 있는지 확인
2. 필요한 의존성이 모두 설치되어 있는지 확인
3. Python 버전이 3.6 이상인지 확인
