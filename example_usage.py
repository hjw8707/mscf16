#!/usr/bin/env python3
"""
MSCF-16 NIM Device Usage Examples

This script demonstrates basic usage for controlling MSCF-16 device.
"""

from mscf16_controller import MSCF16Controller, MSCF16Error


def basic_usage_example():
    """Basic usage example"""
    print("=== MSCF-16 Basic Usage Example ===")

    # Method 1: General usage
    print("\n1. General Usage:")
    controller = MSCF16Controller(port='COM3', baudrate=9600)

    try:
        controller.connect()
        print("Connected to device.")

        # Basic settings
        controller.set_coincidence_window(128)
        controller.set_shaper_offset(100)
        controller.set_threshold_offset(100)

        # Channel-specific settings
        for channel in range(1, 5):
            controller.set_threshold(channel, 100 + channel * 10)
            controller.set_pz_value(channel, 80 + channel * 5)

        # Group-specific settings
        for group in range(1, 3):
            controller.set_shaping_time(group, group * 3)
            controller.set_gain(group, group * 2)

        # Get device information
        version = controller.get_version()
        print(f"Firmware version: {version}")

    except MSCF16Error as e:
        print(f"Error occurred: {e}")
    finally:
        controller.disconnect()
        print("Connection closed.")


def context_manager_example():
    """Context manager usage example"""
    print("\n2. Context Manager Usage:")

    try:
        with MSCF16Controller(port='COM3', baudrate=9600) as controller:
            print("Connected to device (auto-connect).")

            # Common mode settings
            controller.set_threshold(17, 150)  # Common threshold for all channels
            controller.set_pz_value(17, 120)  # Common pz for all channels

            # Group common settings
            controller.set_shaping_time(5, 10)  # Common shaping time for all groups
            controller.set_gain(5, 8)          # Common gain for all groups

            # Mode settings
            controller.set_single_channel_mode(False)
            controller.set_ecl_delay(True)
            controller.set_blr_mode(True)

            # Multiplicity settings
            controller.set_multiplicity_borders(5, 2)

            print("Settings completed.")

    except MSCF16Error as e:
        print(f"Error occurred: {e}")

    print("Connection automatically closed.")


def advanced_usage_example():
    """Advanced usage example"""
    print("\n3. Advanced Usage Example:")

    controller = MSCF16Controller(port='COM3', baudrate=9600)

    try:
        controller.connect()

        # Display all settings
        print("Current settings:")
        setup_info = controller.display_setup()
        print(setup_info)

        # Activate RC mode
        controller.switch_rc_mode_on()
        print("RC mode activated.")

        # Advanced parameter settings
        controller.set_timing_filter(2)
        controller.set_blr_threshold(200)

        # Set automatic pz for specific channels
        controller.set_automatic_pz(1)
        controller.set_automatic_pz(2)

        # Set monitor channel
        controller.set_monitor_channel(1)

        # Copy settings to front panel
        controller.copy_rc_to_front_panel()
        print("Settings copied to front panel.")

        # Change baud rate (Warning: may disconnect)
        print("Changing baud rate to 19200...")
        controller.set_baud_rate(2)  # 19200 baud

    except MSCF16Error as e:
        print(f"Error occurred: {e}")
    finally:
        controller.disconnect()


def error_handling_example():
    """Error handling example"""
    print("\n4. Error Handling Example:")

    controller = MSCF16Controller(port='COM3', baudrate=9600)

    try:
        controller.connect()

        # Try to cause error with invalid parameters
        try:
            controller.set_threshold(0, 128)  # Invalid channel
        except ValueError as e:
            print(f"Expected error: {e}")

        try:
            controller.set_threshold(1, 300)  # Invalid value
        except ValueError as e:
            print(f"Expected error: {e}")

        try:
            controller.set_multiplicity_borders(10, 5)  # Invalid multiplicity
        except ValueError as e:
            print(f"Expected error: {e}")

        # Try to execute command when disconnected
        controller.disconnect()
        try:
            controller.set_threshold(1, 128)
        except MSCF16Error as e:
            print(f"Expected error: {e}")

    except MSCF16Error as e:
        print(f"Connection error: {e}")


if __name__ == "__main__":
    print("MSCF-16 NIM Device Usage Examples")
    print("=" * 50)

    # Examples run without actual device connection
    print("Note: These examples run without an actual device.")
    print("Please specify the correct serial port when using with actual device.")
    print()

    basic_usage_example()
    context_manager_example()
    advanced_usage_example()
    error_handling_example()

    print("\nAll examples completed.")
    print("When using with actual device, please set the port name correctly:")
    print("- Windows: COM1, COM2, COM3, ...")
    print("- Linux: /dev/ttyUSB0, /dev/ttyACM0, ...")
    print("- macOS: /dev/cu.usbserial-*, /dev/cu.usbmodem-*, ...")
