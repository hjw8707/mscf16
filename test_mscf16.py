#!/usr/bin/env python3
"""
MSCF-16 NIM Device Test Script

This script demonstrates how to use the MSCF-16 controller library
and provides basic functionality testing.
"""

import sys
import time
from mscf16_controller import MSCF16Controller, MSCF16Error


def test_basic_commands(controller):
    """Test basic commands that don't require specific hardware responses"""
    print("=== 기본 명령어 테스트 ===")

    try:
        # Get version
        print("펌웨어 버전 요청...")
        version = controller.get_version()
        print(f"버전: {version}")

        # Display setup
        print("\n설정 정보 표시...")
        setup = controller.display_setup()
        print(f"설정: {setup}")

        # Test parameter validation
        print("\n=== 파라미터 검증 테스트 ===")

        # Test valid commands
        print("유효한 명령어 테스트...")
        controller.set_coincidence_window(128)
        controller.set_shaper_offset(100)
        controller.set_threshold_offset(100)
        controller.set_threshold(1, 128)
        controller.set_pz_value(1, 100)
        controller.set_shaping_time(1, 8)
        controller.set_gain(1, 8)
        print("✓ 모든 유효한 명령어가 성공적으로 실행되었습니다.")

        # Test invalid parameters
        print("\n무효한 파라미터 테스트...")
        try:
            controller.set_threshold(0, 128)  # Invalid channel
            print("✗ 채널 검증 실패")
        except ValueError as e:
            print(f"✓ 채널 검증 성공: {e}")

        try:
            controller.set_threshold(1, 300)  # Invalid value
            print("✗ 값 검증 실패")
        except ValueError as e:
            print(f"✓ 값 검증 성공: {e}")

        try:
            controller.set_multiplicity_borders(10, 5)  # Invalid hi value
            print("✗ multiplicity 검증 실패")
        except ValueError as e:
            print(f"✓ multiplicity 검증 성공: {e}")

    except MSCF16Error as e:
        print(f"명령어 실행 오류: {e}")


def test_channel_operations(controller):
    """Test channel-specific operations"""
    print("\n=== 채널별 작업 테스트 ===")

    try:
        # Test individual channel settings
        for channel in range(1, 5):  # Test first 4 channels
            print(f"채널 {channel} 설정...")
            controller.set_threshold(channel, 100 + channel * 10)
            controller.set_pz_value(channel, 80 + channel * 5)
            controller.set_monitor_channel(channel)
            time.sleep(0.1)  # Small delay between commands

        # Test common mode settings
        print("공통 모드 설정...")
        controller.set_threshold(17, 150)  # Common threshold
        controller.set_pz_value(17, 120)   # Common pz

        print("✓ 채널별 작업이 성공적으로 완료되었습니다.")

    except MSCF16Error as e:
        print(f"채널 작업 오류: {e}")


def test_group_operations(controller):
    """Test group-specific operations"""
    print("\n=== 그룹별 작업 테스트 ===")

    try:
        # Test individual group settings
        for group in range(1, 5):  # Test all 4 groups
            print(f"그룹 {group} 설정...")
            controller.set_shaping_time(group, group * 2)
            controller.set_gain(group, group * 2)
            time.sleep(0.1)  # Small delay between commands

        # Test common mode settings
        print("공통 모드 설정...")
        controller.set_shaping_time(5, 10)  # Common shaping time
        controller.set_gain(5, 10)         # Common gain

        print("✓ 그룹별 작업이 성공적으로 완료되었습니다.")

    except MSCF16Error as e:
        print(f"그룹 작업 오류: {e}")


def test_mode_settings(controller):
    """Test mode and control settings"""
    print("\n=== 모드 및 제어 설정 테스트 ===")

    try:
        # Test mode settings
        print("모드 설정...")
        controller.set_single_channel_mode(True)
        controller.set_ecl_delay(False)
        controller.set_blr_mode(True)

        # Test multiplicity settings
        print("Multiplicity 설정...")
        controller.set_multiplicity_borders(5, 2)
        controller.set_multiplicity_borders(9, 1)  # Test infinite

        # Test control commands
        print("제어 명령어...")
        controller.switch_rc_mode_on()
        time.sleep(0.1)
        controller.switch_rc_mode_off()

        print("✓ 모드 및 제어 설정이 성공적으로 완료되었습니다.")

    except MSCF16Error as e:
        print(f"모드 설정 오류: {e}")


def interactive_mode(controller):
    """Interactive mode for manual testing"""
    print("\n=== 대화형 모드 ===")
    print("수동으로 명령어를 테스트할 수 있습니다.")
    print("명령어 형식: <명령어> <파라미터1> <파라미터2> ...")
    print("예: ST 1 128 (채널 1에 threshold 128 설정)")
    print("종료하려면 'quit' 또는 'exit' 입력")
    print("도움말을 보려면 'help' 입력")

    while True:
        try:
            command = input("\n명령어 입력: ").strip()

            if command.lower() in ['quit', 'exit']:
                break
            elif command.lower() == 'help':
                print_help()
                continue
            elif not command:
                continue

            # Send command directly
            response = controller._send_command(command)
            print(f"응답: {response}")

        except KeyboardInterrupt:
            print("\n대화형 모드를 종료합니다.")
            break
        except Exception as e:
            print(f"오류: {e}")


def print_help():
    """Print help information"""
    print("\n=== 사용 가능한 명령어 ===")
    print("SC <value>           - Set coincidence window (0-255)")
    print("SSO <value>          - Set shaper offset (0-200)")
    print("STO <value>          - Set threshold offset (0-200)")
    print("ST <channel> <value> - Set threshold (channel: 1-17, value: 0-255)")
    print("SP <channel> <value> - Set pz value (channel: 1-17, value: 0-255)")
    print("SS <group> <value>   - Set shaping time (group: 1-5, value: 0-15)")
    print("SG <group> <value>   - Set gain (group: 1-5, value: 0-15)")
    print("MC <channel>         - Set monitor channel (1-16)")
    print("SM <hi> <lo>         - Set multiplicity borders (hi: 1-9, lo: 1-8)")
    print("SI <0/1>             - Single channel mode")
    print("SE <0/1>             - ECL delay")
    print("SBL <0/1>           - BLR mode")
    print("ON/OFF               - RC mode on/off")
    print("DS                   - Display setup")
    print("V                    - Get version")


def main():
    """Main test function"""
    print("MSCF-16 NIM Device 테스트 스크립트")
    print("=" * 50)

    # Get port from command line argument or use default
    if len(sys.argv) > 1:
        port = sys.argv[1]
    else:
        port = input("시리얼 포트를 입력하세요 (예: COM3, /dev/ttyUSB0): ").strip()
        if not port:
            print("포트가 지정되지 않았습니다. 테스트를 종료합니다.")
            return

    print(f"포트: {port}")

    # Initialize controller
    try:
        controller = MSCF16Controller(port=port, baudrate=9600)
        print("컨트롤러가 초기화되었습니다.")

        # Connect to device
        print("장치에 연결 중...")
        controller.connect()
        print("✓ 장치에 성공적으로 연결되었습니다.")

        # Run tests
        test_basic_commands(controller)
        test_channel_operations(controller)
        test_group_operations(controller)
        test_mode_settings(controller)

        # Ask for interactive mode
        if input("\n대화형 모드를 시작하시겠습니까? (y/n): ").lower().startswith('y'):
            interactive_mode(controller)

        print("\n테스트가 완료되었습니다.")

    except MSCF16Error as e:
        print(f"연결 오류: {e}")
        print("장치가 연결되어 있는지, 포트가 올바른지 확인하세요.")
    except KeyboardInterrupt:
        print("\n테스트가 중단되었습니다.")
    finally:
        if 'controller' in locals():
            controller.disconnect()
            print("연결이 종료되었습니다.")


if __name__ == "__main__":
    main()
