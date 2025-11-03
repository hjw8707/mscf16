"""
MHV-4 NIM Device Serial Communication Controller

This module provides a Python interface for controlling the MHV-4 NIM device
via serial communication.
"""

import serial
import time
from typing import Optional, Union, Tuple
from mhv4_constants import Commands, Parameters, ErrorMessages


class MHV4Error(Exception):
    """Custom exception for MHV-4 device errors"""
    pass


class MHV4Controller:
    """
    MHV-4 NIM Device Controller

    Provides methods to control the MHV-4 device via serial communication.
    Commands are automatically terminated (no explicit terminator needed).
    Input characters are echoed by the device.
    """

    def __init__(self, port: str, baudrate: int = 9600, timeout: float = 1.0):
        """
        Initialize the MHV-4 controller

        Args:
            port: Serial port name (e.g., 'COM3' on Windows, '/dev/ttyUSB0' on Linux)
            baudrate: Baud rate (default: 9600, fixed for MHV-4)
            timeout: Serial communication timeout in seconds
        """
        self.port = port
        self.baudrate = baudrate  # Fixed at 9600 for MHV-4
        self.timeout = timeout
        self.serial_connection: Optional[serial.Serial] = None
        self.is_connected = False

    def connect(self) -> bool:
        """
        Connect to the MHV-4 device

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

            # Clear any pending data
            self.serial_connection.reset_input_buffer()
            self.serial_connection.reset_output_buffer()

            self.is_connected = True
            return True

        except serial.SerialException as e:
            raise MHV4Error(f"Failed to connect to device: {e}")

    def disconnect(self):
        """Disconnect from the MHV-4 device"""
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()
        self.is_connected = False

    def _send_command(self, command: str, read_response: bool = True) -> str:
        """
        Send a command to the device and return the response

        Args:
            command: Command string to send
            read_response: Whether to read and return response

        Returns:
            Response from the device (if read_response is True)

        Raises:
            MHV4Error: If device is not connected or command fails
        """
        if not self.is_connected or not self.serial_connection:
            raise MHV4Error(ErrorMessages.DEVICE_NOT_CONNECTED)

        try:
            # Send command (no explicit terminator needed)
            full_command = command + '\r'
            self.serial_connection.write(full_command.encode('ascii'))
            self.serial_connection.flush()

            if not read_response:
                return ""

            # Wait a bit for response
            time.sleep(0.1)

            # Read response (device echoes input, then sends response)
            # May need to read echo first, then actual response
            response = ""
            response = self.serial_connection.read_all().decode('ascii')
            response = response.split('\n\r') # [0] is the echo, [1] is the response, [2] is the prompt

            return response[1]

        except serial.SerialException as e:
            raise MHV4Error(f"Serial communication error: {e}")

    def _validate_channel(self, channel: Union[int, str], allow_all: bool = False) -> str:
        """
        Validate and normalize channel number

        Args:
            channel: Channel number (0-3) or '4'/'a' for all
            allow_all: Whether to allow 'all channels' option

        Returns:
            Normalized channel string
        """
        if allow_all and (channel == 4 or str(channel).lower() == 'a'):
            return 'a'

        if isinstance(channel, str):
            channel = int(channel)

        if not (0 <= channel <= 3):
            raise ValueError(ErrorMessages.INVALID_CHANNEL)

        return str(channel)

    # Set Commands

    def turn_on(self, channel: Union[int, str]) -> str:
        """
        Turn channel on

        Args:
            channel: Channel number (0-3) or 'a'/'4' for all channels

        Returns:
            Response from device
        """
        ch = self._validate_channel(channel, allow_all=True)
        return self._send_command(f"{Commands.ON} {ch}")

    def turn_off(self, channel: Union[int, str]) -> str:
        """
        Turn channel off

        Args:
            channel: Channel number (0-3) or 'a'/'4' for all channels

        Returns:
            Response from device
        """
        ch = self._validate_channel(channel, allow_all=True)
        return self._send_command(f"{Commands.OFF} {ch}")

    def set_voltage(self, channel: Union[int, str], voltage_01v: int) -> str:
        """
        Set channel voltage

        Args:
            channel: Channel number (0-3)
            voltage_01v: Voltage in 0.1V units (e.g., 4000 = 400V)

        Returns:
            Response from device
        """
        ch = self._validate_channel(channel, allow_all=False)
        if not (Parameters.VOLTAGE_MIN <= voltage_01v <= Parameters.VOLTAGE_MAX):
            raise ValueError(ErrorMessages.INVALID_VOLTAGE)
        return self._send_command(f"{Commands.SU} {ch} {voltage_01v:04d}")

    def set_voltage_limit(self, channel: Union[int, str], voltage_limit_01v: int) -> str:
        """
        Set channel voltage limit

        Args:
            channel: Channel number (0-3)
            voltage_limit_01v: Voltage limit in 0.1V units

        Returns:
            Response from device
        """
        ch = self._validate_channel(channel, allow_all=False)
        if not (Parameters.VOLTAGE_LIMIT_MIN <= voltage_limit_01v <= Parameters.VOLTAGE_LIMIT_MAX):
            raise ValueError(ErrorMessages.INVALID_VOLTAGE_LIMIT)
        return self._send_command(f"{Commands.SUL} {ch} {voltage_limit_01v:04d}")

    def set_current_limit(self, channel: Union[int, str], current_limit_na: int) -> str:
        """
        Set channel current limit

        Args:
            channel: Channel number (0-3)
            current_limit_na: Current limit in nA units

        Returns:
            Response from device
        """
        ch = self._validate_channel(channel, allow_all=False)
        if not (Parameters.CURRENT_LIMIT_MIN <= current_limit_na <= Parameters.CURRENT_LIMIT_MAX):
            raise ValueError(ErrorMessages.INVALID_CURRENT_LIMIT)
        return self._send_command(f"{Commands.SIL} {ch} {current_limit_na:05d}")

    def set_polarity(self, channel: Union[int, str], polarity: Union[str, int]) -> str:
        """
        Set channel polarity

        Args:
            channel: Channel number (0-3)
            polarity: 'p'/'+'/'1' for positive, 'n'/'-'/'0' for negative

        Returns:
            Response from device

        Note:
            When HV is on, it will automatically turn off, HV preset is set to 0V,
            and polarity changes after HV is turned off. After change, preset must
            be set again to desired value.
        """
        ch = self._validate_channel(channel, allow_all=False)

        # Normalize polarity
        polarity_str = str(polarity).lower()
        if polarity_str in Parameters.POLARITY_POSITIVE:
            pol = 'p'
        elif polarity_str in Parameters.POLARITY_NEGATIVE:
            pol = 'n'
        else:
            raise ValueError(ErrorMessages.INVALID_POLARITY)

        return self._send_command(f"{Commands.SP} {ch} {pol}")

    def set_auto_shutdown(self, channel: Union[int, str], enable: bool) -> str:
        """
        Set auto shutdown for channel

        Args:
            channel: Channel number (0-3)
            enable: True to enable, False to disable

        Returns:
            Response from device
        """
        ch = self._validate_channel(channel, allow_all=False)
        value = 1 if enable else 0
        return self._send_command(f"{Commands.AS} {ch} {value}")

    def set_temperature_compensation(self, channel: Union[int, str],
                                    ntc_channel: Union[int, str, None] = None) -> str:
        """
        Set temperature compensation for channel

        Args:
            channel: Channel number (0-3)
            ntc_channel: NTC channel number (0-3) or '-'/'4'/'None' to disable

        Returns:
            Response from device
        """
        ch = self._validate_channel(channel, allow_all=False)

        if ntc_channel is None or str(ntc_channel).lower() in ['-', '4']:
            ntc = '-'
        else:
            ntc = self._validate_channel(ntc_channel, allow_all=False)

        return self._send_command(f"{Commands.STC} {ch} {ntc}")

    def set_reference_temperature(self, channel: Union[int, str], temp_01c: int) -> str:
        """
        Set reference temperature for channel

        Args:
            channel: Channel number (0-3)
            temp_01c: Temperature in 0.1°C units (e.g., 285 = 28.5°C)

        Returns:
            Response from device
        """
        ch = self._validate_channel(channel, allow_all=False)
        if not (Parameters.TEMPERATURE_MIN <= temp_01c <= Parameters.TEMPERATURE_MAX):
            raise ValueError(ErrorMessages.INVALID_TEMPERATURE)
        return self._send_command(f"{Commands.STO} {ch} {temp_01c:03d}")

    def set_temperature_slope(self, channel: Union[int, str], slope_mv_per_c: int) -> str:
        """
        Set temperature compensation slope for channel

        Args:
            channel: Channel number (0-3)
            slope_mv_per_c: Slope in mV/°C (e.g., 800 = 0.8V/°C, -1200 = -1.2V/°C)

        Returns:
            Response from device
        """
        ch = self._validate_channel(channel, allow_all=False)
        if not (Parameters.TEMPERATURE_SLOPE_MIN <= slope_mv_per_c <= Parameters.TEMPERATURE_SLOPE_MAX):
            raise ValueError(ErrorMessages.INVALID_TEMPERATURE_SLOPE)
        return self._send_command(f"{Commands.STS} {ch} {slope_mv_per_c:04d}")

    def set_ramp_speed(self, speed: int) -> str:
        """
        Set HV ramp speed

        Args:
            speed: 0=5V/s, 1=25V/s, 2=100V/s, 3=500V/s

        Returns:
            Response from device
        """
        if speed not in Parameters.RAMP_SPEED_OPTIONS:
            raise ValueError(ErrorMessages.INVALID_RAMP_SPEED)
        return self._send_command(f"{Commands.SRA} {speed}")

    # Read Commands

    def read_voltage(self, channel: Union[int, str]) -> str:
        """
        Read channel voltage

        Args:
            channel: Channel number (0-3)

        Returns:
            Voltage reading from device
        """
        ch = self._validate_channel(channel, allow_all=False)
        return self._send_command(f"{Commands.RU} {ch}")

    def read_voltage_preset(self, channel: Union[int, str]) -> str:
        """
        Read channel voltage preset

        Args:
            channel: Channel number (0-3)

        Returns:
            Voltage preset reading from device
        """
        ch = self._validate_channel(channel, allow_all=False)
        return self._send_command(f"{Commands.RUP} {ch}")

    def read_voltage_limit(self, channel: Union[int, str]) -> str:
        """
        Read channel voltage limit

        Args:
            channel: Channel number (0-3)

        Returns:
            Voltage limit reading from device
        """
        ch = self._validate_channel(channel, allow_all=False)
        return self._send_command(f"{Commands.RUL} {ch}")

    def read_current(self, channel: Union[int, str]) -> str:
        """
        Read channel current

        Args:
            channel: Channel number (0-3)

        Returns:
            Current reading from device
        """
        ch = self._validate_channel(channel, allow_all=False)
        return self._send_command(f"{Commands.RI} {ch}")

    def read_current_limit(self, channel: Union[int, str]) -> str:
        """
        Read channel current limit

        Args:
            channel: Channel number (0-3)

        Returns:
            Current limit reading from device
        """
        ch = self._validate_channel(channel, allow_all=False)
        return self._send_command(f"{Commands.RIL} {ch}")

    def read_polarity(self, channel: Union[int, str]) -> str:
        """
        Read channel polarity

        Args:
            channel: Channel number (0-3)

        Returns:
            Polarity reading from device
        """
        ch = self._validate_channel(channel, allow_all=False)
        return self._send_command(f"{Commands.RP} {ch}")

    def read_temperature_compensation(self, channel: Union[int, str]) -> str:
        """
        Read temperature compensation settings for channel

        Args:
            channel: Channel number (0-3)

        Returns:
            Temperature compensation settings from device
        """
        ch = self._validate_channel(channel, allow_all=False)
        return self._send_command(f"{Commands.RTC} {ch}")

    def read_temperature(self, input_channel: Union[int, str]) -> str:
        """
        Read temperature from input

        Args:
            input_channel: Input channel number (0-3)

        Returns:
            Temperature reading from device
        """
        ch = self._validate_channel(input_channel, allow_all=False)
        return self._send_command(f"{Commands.RT} {ch}")

    def read_ramp_speed(self) -> str:
        """
        Read HV ramp speed

        Returns:
            Ramp speed reading from device
        """
        return self._send_command(Commands.RRA)

    # Context manager support
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

if __name__ == "__main__":
    controller = MHV4Controller(port="/dev/tty.usbserial-0120182", baudrate=9600)
    controller.connect()
    print(controller._send_command("SP 0 n"))
    print(controller._send_command("SP 0 p"))

    controller.turn_on(0)
    controller.turn_on(1)
    controller.turn_on(2)
    controller.turn_on(3)
    print(controller.read_voltage(0))
    print(controller.read_voltage(1))
    print(controller.read_voltage(2))
    print(controller.read_voltage(3))

    controller.turn_off(0)
    controller.turn_off(1)
    controller.turn_off(2)
    controller.turn_off(3)


    print(controller.read_ramp_speed())
    print(controller.read_temperature(0))
    print(controller.read_temperature_compensation(1))
    controller.disconnect()