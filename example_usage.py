#!/usr/bin/env python3
"""
MSCF-16 NIM Device 사용 예제

이 스크립트는 MSCF-16 장치를 제어하는 기본적인 사용법을 보여줍니다.
"""

from mscf16_controller import MSCF16Controller, MSCF16Error


def basic_usage_example():
    """기본 사용법 예제"""
    print("=== MSCF-16 기본 사용법 예제 ===")

    # 방법 1: 일반적인 사용법
    print("\n1. 일반적인 사용법:")
    controller = MSCF16Controller(port='COM3', baudrate=9600)

    try:
        controller.connect()
        print("장치에 연결되었습니다.")

        # 기본 설정
        controller.set_coincidence_window(128)
        controller.set_shaper_offset(100)
        controller.set_threshold_offset(100)

        # 채널별 설정
        for channel in range(1, 5):
            controller.set_threshold(channel, 100 + channel * 10)
            controller.set_pz_value(channel, 80 + channel * 5)

        # 그룹별 설정
        for group in range(1, 3):
            controller.set_shaping_time(group, group * 3)
            controller.set_gain(group, group * 2)

        # 장치 정보 확인
        version = controller.get_version()
        print(f"펌웨어 버전: {version}")

    except MSCF16Error as e:
        print(f"오류 발생: {e}")
    finally:
        controller.disconnect()
        print("연결이 종료되었습니다.")


def context_manager_example():
    """Context manager 사용법 예제"""
    print("\n2. Context Manager 사용법:")

    try:
        with MSCF16Controller(port='COM3', baudrate=9600) as controller:
            print("장치에 연결되었습니다 (자동 연결).")

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

            print("설정이 완료되었습니다.")

    except MSCF16Error as e:
        print(f"오류 발생: {e}")

    print("자동으로 연결이 종료되었습니다.")


def advanced_usage_example():
    """고급 사용법 예제"""
    print("\n3. 고급 사용법 예제:")

    controller = MSCF16Controller(port='COM3', baudrate=9600)

    try:
        controller.connect()

        # 모든 설정을 표시
        print("현재 설정:")
        setup_info = controller.display_setup()
        print(setup_info)

        # RC 모드 활성화
        controller.switch_rc_mode_on()
        print("RC 모드가 활성화되었습니다.")

        # 고급 파라미터 설정
        controller.set_timing_filter(2)
        controller.set_blr_threshold(200)

        # 특정 채널에 자동 pz 설정
        controller.set_automatic_pz(1)
        controller.set_automatic_pz(2)

        # 모니터 채널 설정
        controller.set_monitor_channel(1)

        # 설정을 프론트 패널에 복사
        controller.copy_rc_to_front_panel()
        print("설정이 프론트 패널에 복사되었습니다.")

        # Baud rate 변경 (주의: 연결이 끊어질 수 있음)
        print("Baud rate를 19200으로 변경합니다...")
        controller.set_baud_rate(2)  # 19200 baud

    except MSCF16Error as e:
        print(f"오류 발생: {e}")
    finally:
        controller.disconnect()


def error_handling_example():
    """에러 처리 예제"""
    print("\n4. 에러 처리 예제:")

    controller = MSCF16Controller(port='COM3', baudrate=9600)

    try:
        controller.connect()

        # 잘못된 파라미터로 에러 발생 시도
        try:
            controller.set_threshold(0, 128)  # 잘못된 채널
        except ValueError as e:
            print(f"예상된 에러: {e}")

        try:
            controller.set_threshold(1, 300)  # 잘못된 값
        except ValueError as e:
            print(f"예상된 에러: {e}")

        try:
            controller.set_multiplicity_borders(10, 5)  # 잘못된 multiplicity
        except ValueError as e:
            print(f"예상된 에러: {e}")

        # 연결되지 않은 상태에서 명령 실행 시도
        controller.disconnect()
        try:
            controller.set_threshold(1, 128)
        except MSCF16Error as e:
            print(f"예상된 에러: {e}")

    except MSCF16Error as e:
        print(f"연결 오류: {e}")


if __name__ == "__main__":
    print("MSCF-16 NIM Device 사용 예제")
    print("=" * 50)

    # 실제 장치가 연결되어 있지 않으므로 예제만 표시
    print("주의: 이 예제는 실제 장치 없이 실행됩니다.")
    print("실제 사용 시에는 올바른 시리얼 포트를 지정하세요.")
    print()

    basic_usage_example()
    context_manager_example()
    advanced_usage_example()
    error_handling_example()

    print("\n모든 예제가 완료되었습니다.")
    print("실제 장치를 사용할 때는 포트 이름을 올바르게 설정하세요:")
    print("- Windows: COM1, COM2, COM3, ...")
    print("- Linux: /dev/ttyUSB0, /dev/ttyACM0, ...")
    print("- macOS: /dev/cu.usbserial-*, /dev/cu.usbmodem-*, ...")
