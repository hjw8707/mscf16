"""
MSCF-16 NIM Device Constants and Parameters

This module contains all the command constants and parameter definitions
for the MSCF-16 NIM device serial communication.
"""

# Command constants
class Commands:
    """MSCF-16 command constants"""

    # Coincidence and timing commands
    SC = "SC"      # Set coincidence time window
    SSO = "SSO"    # Set shaper offset
    STO = "STO"    # Set threshold offset
    SBT = "SBT"    # Set BLR threshold
    SF = "SF"      # Timing filter integration time

    # Channel-specific commands
    ST = "ST"      # Set threshold value
    SP = "SP"      # Set pz value
    MC = "MC"      # Set monitor output to channel
    AP = "AP"      # Automatic pz setting for channel

    # Group-specific commands
    SS = "SS"      # Set shaping time for a group
    SG = "SG"      # Set Gain for groups of 4 channels

    # Multiplicity commands
    SM = "SM"      # Set multiplicity borders

    # Mode commands
    SI = "SI"      # Single channel mode
    SE = "SE"      # ECL delay
    SBL = "SBL"    # Switch BLR on/off

    # Control commands
    ON = "ON"      # Switch RC mode on
    OFF = "OFF"    # Switch RC mode off

    # Utility commands
    DS = "DS"      # Display Set up
    SB = "SB"      # Set Baud rate
    CPY_F = "CPY F"  # Copy front panel settings to RC memory
    CPY_R = "CPY R"  # Copy RC settings to front panel memory
    V = "V"        # Display firmware version


# Parameter ranges and defaults
class Parameters:
    """Parameter ranges and default values"""

    # Channel ranges
    CHANNELS = list(range(1, 17))  # Channels 1-16
    COMMON_CHANNEL = 17            # Common mode for thresholds and pz

    # Group ranges
    GROUPS = list(range(1, 5))     # Groups 1-4
    COMMON_GROUP = 5               # Common mode for shaping time and gain

    # Parameter ranges
    COINCIDENCE_WINDOW = (0, 255)
    SHAPER_OFFSET = (0, 200)
    THRESHOLD_OFFSET = (0, 200)
    BLR_THRESHOLD = (0, 255)
    THRESHOLD_VALUE = (0, 255)
    PZ_VALUE = (0, 255)
    SHAPING_TIME = (0, 15)
    GAIN_VALUE = (0, 15)
    MULTIPLICITY_BORDER = (1, 8)
    MULTIPLICITY_INFINITE = 9
    TIMING_FILTER = (0, 3)

    # Default values
    DEFAULT_SHAPER_OFFSET = 100
    DEFAULT_THRESHOLD_OFFSET = 100

    # Baud rate options
    BAUD_RATES = {
        1: 9600,    # Power-Up default
        2: 19200,
        3: 28400,
        4: 57600,
        5: 115200
    }

    DEFAULT_BAUD_RATE = 9600


# Error messages
class ErrorMessages:
    """Error messages for various conditions"""

    INVALID_CHANNEL = "Channel must be between 1-16"
    INVALID_COMMON_CHANNEL = "Channel must be between 1-17 (17 = common)"
    INVALID_GROUP = "Group must be between 1-4"
    INVALID_COMMON_GROUP = "Group must be between 1-5 (5 = common)"
    INVALID_RANGE = "Value out of valid range"
    INVALID_BAUD_RATE = "Invalid baud rate option"
    DEVICE_NOT_CONNECTED = "Device is not connected"
    COMMAND_FAILED = "Command execution failed"
    INVALID_RESPONSE = "Invalid response from device"
