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
    print("=== Basic Command Test ===")

    try:
        # Get version
        print("Requesting firmware version...")
        version = controller.get_version()
        print(f"Version: {version}")

        # Display setup
        print("\nDisplaying setup information...")
        setup = controller.display_setup()
        print(f"Setup: {setup}")

        # Test parameter validation
        print("\n=== Parameter Validation Test ===")

        # Test valid commands
        print("Testing valid commands...")
        controller.set_coincidence_window(128)
        controller.set_shaper_offset(100)
        controller.set_threshold_offset(100)
        controller.set_threshold(1, 128)
        controller.set_pz_value(1, 100)
        controller.set_shaping_time(1, 8)
        controller.set_gain(1, 8)
        print("✓ All valid commands executed successfully.")

        # Test invalid parameters
        print("\nTesting invalid parameters...")
        try:
            controller.set_threshold(0, 128)  # Invalid channel
            print("✗ Channel validation failed")
        except ValueError as e:
            print(f"✓ Channel validation successful: {e}")

        try:
            controller.set_threshold(1, 300)  # Invalid value
            print("✗ Value validation failed")
        except ValueError as e:
            print(f"✓ Value validation successful: {e}")

        try:
            controller.set_multiplicity_borders(10, 5)  # Invalid hi value
            print("✗ Multiplicity validation failed")
        except ValueError as e:
            print(f"✓ Multiplicity validation successful: {e}")

    except MSCF16Error as e:
        print(f"Command execution error: {e}")


def test_channel_operations(controller):
    """Test channel-specific operations"""
    print("\n=== Channel Operations Test ===")

    try:
        # Test individual channel settings
        for channel in range(1, 5):  # Test first 4 channels
            print(f"Setting channel {channel}...")
            controller.set_threshold(channel, 100 + channel * 10)
            controller.set_pz_value(channel, 80 + channel * 5)
            controller.set_monitor_channel(channel)
            time.sleep(0.1)  # Small delay between commands

        # Test common mode settings
        print("Setting common mode...")
        controller.set_threshold(17, 150)  # Common threshold
        controller.set_pz_value(17, 120)   # Common pz

        print("✓ Channel operations completed successfully.")

    except MSCF16Error as e:
        print(f"Channel operation error: {e}")


def test_group_operations(controller):
    """Test group-specific operations"""
    print("\n=== Group Operations Test ===")

    try:
        # Test individual group settings
        for group in range(1, 5):  # Test all 4 groups
            print(f"Setting group {group}...")
            controller.set_shaping_time(group, group * 2)
            controller.set_gain(group, group * 2)
            time.sleep(0.1)  # Small delay between commands

        # Test common mode settings
        print("Setting common mode...")
        controller.set_shaping_time(5, 10)  # Common shaping time
        controller.set_gain(5, 10)         # Common gain

        print("✓ Group operations completed successfully.")

    except MSCF16Error as e:
        print(f"Group operation error: {e}")


def test_mode_settings(controller):
    """Test mode and control settings"""
    print("\n=== Mode and Control Settings Test ===")

    try:
        # Test mode settings
        print("Setting modes...")
        controller.set_single_channel_mode(True)
        controller.set_ecl_delay(False)
        controller.set_blr_mode(True)

        # Test multiplicity settings
        print("Setting multiplicity...")
        controller.set_multiplicity_borders(5, 2)
        controller.set_multiplicity_borders(9, 1)  # Test infinite

        # Test control commands
        print("Control commands...")
        controller.switch_rc_mode_on()
        time.sleep(0.1)
        controller.switch_rc_mode_off()

        print("✓ Mode and control settings completed successfully.")

    except MSCF16Error as e:
        print(f"Mode setting error: {e}")


def interactive_mode(controller):
    """Interactive mode for manual testing"""
    print("\n=== Interactive Mode ===")
    print("You can test commands manually.")
    print("Command format: <command> <parameter1> <parameter2> ...")
    print("Example: ST 1 128 (Set threshold 128 for channel 1)")
    print("Type 'quit' or 'exit' to exit")
    print("Type 'help' for help")

    while True:
        try:
            command = input("\nEnter command: ").strip()

            if command.lower() in ['quit', 'exit']:
                break
            elif command.lower() == 'help':
                print_help()
                continue
            elif not command:
                continue

            # Send command directly
            response = controller._send_command(command)
            print(f"Response: {response}")

        except KeyboardInterrupt:
            print("\nExiting interactive mode.")
            break
        except Exception as e:
            print(f"Error: {e}")


def print_help():
    """Print help information"""
    print("\n=== Available Commands ===")
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
    print("MSCF-16 NIM Device Test Script")
    print("=" * 50)

    # Get port from command line argument or use default
    if len(sys.argv) > 1:
        port = sys.argv[1]
    else:
        port = input("Enter serial port (e.g., COM3, /dev/ttyUSB0): ").strip()
        if not port:
            print("Port not specified. Exiting test.")
            return

    print(f"Port: {port}")

    # Initialize controller
    try:
        controller = MSCF16Controller(port=port, baudrate=9600)
        print("Controller initialized.")

        # Connect to device
        print("Connecting to device...")
        controller.connect()
        print("✓ Successfully connected to device.")

        # Run tests
        test_basic_commands(controller)
        test_channel_operations(controller)
        test_group_operations(controller)
        test_mode_settings(controller)

        # Ask for interactive mode
        if input("\nStart interactive mode? (y/n): ").lower().startswith('y'):
            interactive_mode(controller)

        print("\nTest completed.")

    except MSCF16Error as e:
        print(f"Connection error: {e}")
        print("Please check if device is connected and port is correct.")
    except KeyboardInterrupt:
        print("\nTest interrupted.")
    finally:
        if 'controller' in locals():
            controller.disconnect()
            print("Connection closed.")


if __name__ == "__main__":
    main()
