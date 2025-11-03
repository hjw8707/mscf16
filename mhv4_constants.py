"""
MHV-4 NIM Device Constants and Parameters

This module contains all the command constants and parameter definitions
for the MHV-4 NIM device serial communication.
"""

# Command constants
class Commands:
    """MHV-4 command constants"""

    # Set commands
    ON = "ON"        # Turn channel on
    OFF = "OFF"      # Turn channel off
    SU = "SU"        # Set voltage
    SUL = "SUL"      # Set voltage limit
    SIL = "SIL"      # Set current limit
    SP = "SP"        # Set polarity
    AS = "AS"        # Auto shutdown
    STC = "STC"      # Set temperature compensation
    STO = "STO"      # Set reference temperature
    STS = "STS"      # Set temperature slope
    SRA = "SRA"      # Set ramp speed

    # Read commands
    RU = "RU"        # Read voltage
    RUP = "RUP"      # Read voltage preset
    RUL = "RUL"      # Read voltage limit
    RI = "RI"        # Read current
    RIL = "RIL"      # Read current limit
    RP = "RP"        # Read polarity
    RTC = "RTC"      # Read temperature compensation settings
    RT = "RT"        # Read temperature
    RRA = "RRA"      # Read ramp speed


# Parameter ranges and defaults
class Parameters:
    """Parameter ranges and default values"""

    # Channel ranges
    CHANNELS = list(range(0, 4))  # Channels 0-3
    ALL_CHANNELS = 4               # All channels (use 'a' or '4')

    # Voltage ranges (in 0.1V units)
    VOLTAGE_MIN = 0
    VOLTAGE_MAX = 8000  # 800V maximum

    # Voltage limit ranges (in 0.1V units)
    VOLTAGE_LIMIT_MIN = 0
    VOLTAGE_LIMIT_MAX = 8000

    # Current limit ranges (in nA units)
    CURRENT_LIMIT_MIN = 0
    CURRENT_LIMIT_MAX = 20000  # 20 uA maximum

    # Polarity values
    POLARITY_POSITIVE = ['p', '+', '1']
    POLARITY_NEGATIVE = ['n', '-', '0']

    # Auto shutdown values
    AUTO_SHUTDOWN_ON = 1
    AUTO_SHUTDOWN_OFF = 0

    # Temperature compensation channels
    TEMP_COMP_CHANNELS = list(range(0, 4))  # 0-3
    TEMP_COMP_OFF = ['-', '4']

    # Temperature ranges (in 0.1°C units)
    TEMPERATURE_MIN = -500  # -50°C
    TEMPERATURE_MAX = 1500  # 150°C

    # Temperature slope ranges (in mV/°C)
    TEMPERATURE_SLOPE_MIN = -10000  # -10 V/°C
    TEMPERATURE_SLOPE_MAX = 10000   # 10 V/°C

    # Ramp speed options
    RAMP_SPEED_OPTIONS = {
        0: 5,      # 5 V/s
        1: 25,     # 25 V/s
        2: 100,    # 100 V/s
        3: 500     # 500 V/s
    }

    # Baud rate (fixed)
    BAUD_RATE = 9600


# Error messages
class ErrorMessages:
    """Error messages for various conditions"""

    INVALID_CHANNEL = "Channel must be between 0-3 (or 4/'a' for all channels)"
    INVALID_VOLTAGE = "Voltage must be between 0-5000 (in 0.1V units, max 500V)"
    INVALID_VOLTAGE_LIMIT = "Voltage limit must be between 0-5000 (in 0.1V units)"
    INVALID_CURRENT_LIMIT = "Current limit must be between 0-100000 (in nA units)"
    INVALID_POLARITY = "Polarity must be 'p'/'+'/'1' (positive) or 'n'/'-'/'0' (negative)"
    INVALID_TEMP_COMP = "Temperature compensation channel must be 0-3 or '-'/'4' to disable"
    INVALID_TEMPERATURE = "Temperature must be between -500 to 1500 (in 0.1°C units)"
    INVALID_TEMPERATURE_SLOPE = "Temperature slope must be between -10000 to 10000 (in mV/°C)"
    INVALID_RAMP_SPEED = "Ramp speed must be 0-3 (0=5V/s, 1=25V/s, 2=100V/s, 3=500V/s)"
    DEVICE_NOT_CONNECTED = "Device is not connected"
    COMMAND_FAILED = "Command execution failed"
    INVALID_RESPONSE = "Invalid response from device"