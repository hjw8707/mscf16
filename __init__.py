"""
MSCF-16 NIM Device Serial Communication Library

A Python library for controlling MSCF-16 NIM device via serial communication.
"""

from .mscf16_controller import MSCF16Controller, MSCF16Error
from .mscf16_constants import Commands, Parameters, ErrorMessages

__version__ = "1.0.0"
__author__ = "MSCF-16 Library"

__all__ = [
    'MSCF16Controller',
    'MSCF16Error',
    'Commands',
    'Parameters',
    'ErrorMessages'
]
