"""
MSCF-16 NIM Device Serial Communication Controller

This module provides a Python interface for controlling the MSCF-16 NIM device
via serial communication.
"""

import serial
import time
from typing import Optional, Union, Tuple
from mscf16_constants import Commands, Parameters, ErrorMessages


class MSCF16Error(Exception):
    """Custom exception for MSCF-16 device errors"""
    pass


class MSCF16Controller:
    """
    MSCF-16 NIM Device Controller

    Provides methods to control the MSCF-16 device via serial communication.
    All commands are automatically terminated with carriage return (CR).
    """

    def __init__(self, port: str, baudrate: int = 9600, timeout: float = 1.0):
        """
        Initialize the MSCF-16 controller

        Args:
            port: Serial port name (e.g., 'COM3' on Windows, '/dev/ttyUSB0' on Linux)
            baudrate: Baud rate (default: 9600)
            timeout: Serial communication timeout in seconds
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial_connection: Optional[serial.Serial] = None
        self.is_connected = False

    def connect(self) -> bool:
        """
        Connect to the MSCF-16 device

        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.serial_connection = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=self.timeout
            )

            # Wait for connection to stabilize
            time.sleep(0.1)

            self.is_connected = True
            return True

        except serial.SerialException as e:
            raise MSCF16Error(f"Failed to connect to device: {e}")

    def disconnect(self):
        """Disconnect from the MSCF-16 device"""
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()
        self.is_connected = False

    def _send_command(self, command: str) -> str:
        """
        Send a command to the device and return the response

        Args:
            command: Command string to send

        Returns:
            Response from the device

        Raises:
            MSCF16Error: If device is not connected or command fails
        """
        if not self.is_connected or not self.serial_connection:
            raise MSCF16Error(ErrorMessages.DEVICE_NOT_CONNECTED)

        try:
            # Add carriage return and send command
            full_command = command + '\r'
            self.serial_connection.write(full_command.encode('ascii'))

            # Read response
            response = self.serial_connection.readline().decode('ascii').strip()
            return response

        except serial.SerialException as e:
            raise MSCF16Error(f"Serial communication error: {e}")

    def _validate_channel(self, channel: int, allow_common: bool = False) -> None:
        """Validate channel number"""
        max_channel = Parameters.COMMON_CHANNEL if allow_common else 16
        if not (1 <= channel <= max_channel):
            error_msg = ErrorMessages.INVALID_COMMON_CHANNEL if allow_common else ErrorMessages.INVALID_CHANNEL
            raise ValueError(error_msg)

    def _validate_group(self, group: int, allow_common: bool = False) -> None:
        """Validate group number"""
        max_group = Parameters.COMMON_GROUP if allow_common else 4
        if not (1 <= group <= max_group):
            error_msg = ErrorMessages.INVALID_COMMON_GROUP if allow_common else ErrorMessages.INVALID_GROUP
            raise ValueError(error_msg)

    def _validate_range(self, value: int, min_val: int, max_val: int) -> None:
        """Validate parameter range"""
        if not (min_val <= value <= max_val):
            raise ValueError(ErrorMessages.INVALID_RANGE)

    # Coincidence and timing commands
    def set_coincidence_window(self, value: int) -> str:
        """Set coincidence time window (0-255)"""
        self._validate_range(value, *Parameters.COINCIDENCE_WINDOW)
        return self._send_command(f"{Commands.SC} {value}")

    def set_shaper_offset(self, value: int) -> str:
        """Set shaper offset (0-200)"""
        self._validate_range(value, *Parameters.SHAPER_OFFSET)
        return self._send_command(f"{Commands.SSO} {value}")

    def set_threshold_offset(self, value: int) -> str:
        """Set threshold offset (0-200)"""
        self._validate_range(value, *Parameters.THRESHOLD_OFFSET)
        return self._send_command(f"{Commands.STO} {value}")

    def set_blr_threshold(self, value: int) -> str:
        """Set BLR threshold (0-255)"""
        self._validate_range(value, *Parameters.BLR_THRESHOLD)
        return self._send_command(f"{Commands.SBT} {value}")

    def set_timing_filter(self, value: int) -> str:
        """Set timing filter integration time (0-3)"""
        self._validate_range(value, *Parameters.TIMING_FILTER)
        return self._send_command(f"{Commands.SF} {value}")

    # Channel-specific commands
    def set_threshold(self, channel: int, value: int) -> str:
        """Set threshold value for channel (1-17, where 17=common)"""
        self._validate_channel(channel, allow_common=True)
        self._validate_range(value, *Parameters.THRESHOLD_VALUE)
        return self._send_command(f"{Commands.ST} {channel} {value}")

    def set_pz_value(self, channel: int, value: int) -> str:
        """Set pz value for channel (1-17, where 17=common)"""
        self._validate_channel(channel, allow_common=True)
        self._validate_range(value, *Parameters.PZ_VALUE)
        return self._send_command(f"{Commands.SP} {channel} {value}")

    def set_monitor_channel(self, channel: int) -> str:
        """Set monitor output to channel (1-16)"""
        self._validate_channel(channel, allow_common=False)
        return self._send_command(f"{Commands.MC} {channel}")

    def set_automatic_pz(self, channel: int) -> str:
        """Set automatic pz setting for channel (1-16)"""
        self._validate_channel(channel, allow_common=False)
        return self._send_command(f"{Commands.AP} {channel}")

    def toggle_automatic_pz(self) -> str:
        """Toggle automatic pz setting on/off"""
        return self._send_command(Commands.AP)

    # Group-specific commands
    def set_shaping_time(self, group: int, value: int) -> str:
        """Set shaping time for group (1-5, where 5=common)"""
        self._validate_group(group, allow_common=True)
        self._validate_range(value, *Parameters.SHAPING_TIME)
        return self._send_command(f"{Commands.SS} {group} {value}")

    def set_gain(self, group: int, value: int) -> str:
        """Set gain for group (1-5, where 5=common)"""
        self._validate_group(group, allow_common=True)
        self._validate_range(value, *Parameters.GAIN_VALUE)
        return self._send_command(f"{Commands.SG} {group} {value}")

    # Multiplicity commands
    def set_multiplicity_borders(self, hi: int, lo: int) -> str:
        """Set multiplicity borders (hi: 1-9, lo: 1-8)"""
        if not (1 <= lo <= 8):
            raise ValueError("Low multiplicity must be between 1-8")
        if not (1 <= hi <= 9):
            raise ValueError("High multiplicity must be between 1-9")
        return self._send_command(f"{Commands.SM} {hi} {lo}")

    # Mode commands
    def set_single_channel_mode(self, enable: bool) -> str:
        """Set single channel mode (True/False)"""
        value = 1 if enable else 0
        return self._send_command(f"{Commands.SI} {value}")

    def set_ecl_delay(self, enable: bool) -> str:
        """Set ECL delay (True/False)"""
        value = 1 if enable else 0
        return self._send_command(f"{Commands.SE} {value}")

    def set_blr_mode(self, enable: bool) -> str:
        """Switch BLR on/off (True/False)"""
        value = 1 if enable else 0
        return self._send_command(f"{Commands.SBL} {value}")

    # Control commands
    def switch_rc_mode_on(self) -> str:
        """Switch RC mode on"""
        return self._send_command(Commands.ON)

    def switch_rc_mode_off(self) -> str:
        """Switch RC mode off"""
        return self._send_command(Commands.OFF)

    # Utility commands
    def display_setup(self) -> str:
        """Display all settings (gains, thresholds, pz values, shaping times, etc.)"""
        return self._send_command(Commands.DS)

    def set_baud_rate(self, rate_option: int) -> str:
        """Set baud rate (1-5)"""
        if rate_option not in Parameters.BAUD_RATES:
            raise ValueError(ErrorMessages.INVALID_BAUD_RATE)
        return self._send_command(f"{Commands.SB} {rate_option}")

    def copy_front_panel_to_rc(self) -> str:
        """Copy front panel settings to RC memory"""
        return self._send_command(Commands.CPY_F)

    def copy_rc_to_front_panel(self) -> str:
        """Copy RC settings to front panel memory"""
        return self._send_command(Commands.CPY_R)

    def get_version(self) -> str:
        """Get firmware version"""
        return self._send_command(Commands.V)

    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()

    def __del__(self):
        """Destructor to ensure connection is closed"""
        if hasattr(self, 'is_connected') and self.is_connected:
            self.disconnect()
