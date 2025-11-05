"""
MSCF-16 NIM Device Serial Communication Controller

This module provides a Python interface for controlling the MSCF-16 NIM device
via serial communication.
"""

from multiprocessing import context
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
            self.serial_connection.flush()

            response = ""
            while True:
                response += self.serial_connection.read_all().decode('ascii')
                if response.endswith('>'):
                    break
            response = response.replace('\n', '')
            responses = response.split('\r') # [0] is the echo, [1] is the response, [2] is the prompt
            # Remove empty elements from responses
            responses = [r for r in responses if r.strip()]
            # response[0] is the echo, [1~-2] is the response, [-1] is the prompt
            return responses


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

    def display_setup_parsed(self) -> Tuple[dict, dict, dict]:
        """
        Display all settings (gains, thresholds, pz values, shaping times, etc.) and parse them
        Returns:
            Tuple of (panel_settings, rc_settings, general_settings) dictionaries
        """
        setup = self.display_setup()

        # Common parsing function: parse list and common value for a specific prefix
        # Append common value to the end of each array
        def parse_list_with_common(line, key):
            # e.g. 'gains: 4 5 0 5 c:4'
            vals = []
            cval = None
            # Split values by ":" and find common value directly with c:
            segs = line.split()
            for seg in segs[1:]:  # First element is prefix ('gains:' etc.), so ignore it
                if seg.startswith("c:"):
                    try:
                        cval = int(seg[2:])
                    except ValueError:
                        pass
                elif seg.isdigit():
                    vals.append(int(seg))
            # Add "common" value to the end of each array
            if cval is not None:
                vals.append(cval)
            return {key: vals}

        # prefix:str => (field_name, parse_as_list)
        panel_rc_prefixes = [
            ("gains:", "gains", True),
            ("threshs:", "threshs", True),
            ("upper lim:", "upper_lim", True),
            ("pz:", "pz", True),
            ("shts:", "shts", True),
            ("mult:", "mult", False),
            ("monitor:", "monitor", False),
            ("ECL delay:", "ecl_delay", False),
            ("TF int:", "tf_int", False),
        ]

        def parse_mult(line):
            segs = line.split(":")[1].strip().split()
            if len(segs) == 2:
                hi, lo = int(segs[0]), int(segs[1])
                return {"high": hi, "low": lo}
            return {}

        def parse_monitor(line):
            return int(line.split(":")[1].strip())

        def parse_ecl_delay(line):
            if ':' in line:
                status = line.split(':')[1].strip()
                return status == 'on'
            return None

        def parse_tf_int(line):
            return int(line.split(":")[1].strip())

        def parse_blr(line):
            return 'active' in line

        def parse_single_mode(line):
            return 'single' in line

        def parse_rc_mode(line):
            return 'rc on' in line

        def parse_pz_disp_resolution(line):
            return int(line.split(":")[1].strip())

        def parse_simple_int(line):
            return int(line.split(":")[1].strip())

        def parse_str_val(line):
            return line.split(":")[1].strip()

        # Main parsing loop
        panel_set, rc_set, gen_set = {}, {}, {}
        section = None

        i = 0
        while i < len(setup):
            line = setup[i].strip()
            if line.startswith("MSCF-16 Panel settings"):
                section = "panel"
            elif line.startswith("MSCF-16 rc settings"):
                section = "rc"
            elif line.startswith("MSCF-16 general settings"):
                section = "general"
            elif section in ("panel", "rc"):
                target = panel_set if section == "panel" else rc_set
                for prefix, key, as_list in panel_rc_prefixes:
                    if line.startswith(prefix):
                        if as_list:
                            d = parse_list_with_common(line, key)
                            target.update(d)
                        else:
                            # Handle special keys
                            if key == "mult":
                                target["mult"] = parse_mult(line)
                            elif key == "monitor":
                                target["monitor"] = parse_monitor(line)
                            elif key == "ecl_delay":
                                target["ecl_delay"] = parse_ecl_delay(line)
                            elif key == "tf_int":
                                target["tf_int"] = parse_tf_int(line)
                        break
                else:
                    if "BLR" in line:
                        target["blr_active"] = parse_blr(line)
                    if "single mode" in line or "common mode" in line:
                        target["single_mode"] = parse_single_mode(line)
                    if section == "rc" and ("rc on" in line or "rc off" in line):
                        target["rc_mode"] = parse_rc_mode(line)
                    if section == "rc" and "pz disp resolution" in line:
                        target["pz_disp_resolution"] = parse_pz_disp_resolution(line)
            elif section == "general":
                if line.startswith("BLR thresh:"):
                    gen_set["blr_thresh"] = parse_simple_int(line)
                elif line.startswith("Coincidence time:"):
                    gen_set["coincidence_time"] = parse_simple_int(line)
                elif line.startswith("Sum discr thresh:"):
                    gen_set["sum_discr_thresh"] = parse_simple_int(line)
                elif line.startswith("MSCF-16 software version:"):
                    gen_set["sw_version"] = parse_str_val(line)
                elif line.startswith("MSCF-16 firmware version:"):
                    gen_set["fw_version"] = parse_str_val(line)
            i += 1

        return panel_set, rc_set, gen_set

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

    def get_version_parsed(self) -> Tuple[str, str]: # sw_version, hw_version
        """Get firmware version and parse it"""
        version = self.get_version()
        sw_version = version[1].split(':')[1].strip()
        hw_version = version[2].split(':')[1].strip()
        return sw_version, hw_version

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
    controller = MSCF16Controller(port="/dev/tty.usbserial-1119991", baudrate=9600)
    controller.connect()
    controller.switch_rc_mode_on()
    controller.set_gain(1, 0)
    controller.set_single_channel_mode(True)
    controller.set_ecl_delay(True)
    controller.set_blr_mode(True)
    print(controller.display_setup())
    print(controller.display_setup_parsed())
    controller.disconnect()