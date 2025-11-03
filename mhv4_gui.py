"""
MHV-4 NIM Device GUI Application

PyQt5 기반의 MHV-4 장치 제어 GUI 애플리케이션
프론트패널과 유사한 인터페이스 제공, 여러 모듈 동시 제어 지원
"""

import sys
import serial.tools.list_ports
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                            QHBoxLayout, QTabWidget, QLabel, QPushButton,
                            QComboBox, QSpinBox, QCheckBox, QGroupBox, QDoubleSpinBox,
                            QTextEdit, QStatusBar, QMessageBox, QGridLayout,
                            QLCDNumber, QFrame, QLineEdit)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QColor, QPalette
from typing import Optional
from mhv4_controller import MHV4Controller, MHV4Error
from mhv4_constants import Parameters


class ChannelPanel(QFrame):
    """Individual channel control panel (HV0-HV3)"""

    def __init__(self, channel_num: int, controller: MHV4Controller):
        super().__init__()
        self.channel_num = channel_num
        self.controller = controller
        self.init_ui()
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_readings)

    def init_ui(self):
        """Initialize channel panel UI"""
        self.setFrameStyle(QFrame.Box)
        self.setStyleSheet("""
            QFrame {
                border: 2px solid #666;
                border-radius: 5px;
                background-color: #ffffcc;
                padding: 5px;
            }
        """)

        layout = QVBoxLayout()
        layout.setSpacing(5)
        layout.setContentsMargins(10, 10, 10, 10)

        # Channel label
        channel_label = QLabel(f"HV {self.channel_num}")
        channel_label.setFont(QFont("Arial", 12, QFont.Bold))
        channel_layout = QHBoxLayout()
        channel_layout.addWidget(channel_label)
        channel_layout.addStretch()

        # Polarity indicators
        polarity_layout = QHBoxLayout()
        self.positive_indicator = QLabel("+")
        self.positive_indicator.setFixedSize(20, 20)
        self.positive_indicator.setAlignment(Qt.AlignCenter)
        self.positive_indicator.setStyleSheet("""
            QLabel {
                background-color: #90EE90;
                border: 1px solid #333;
                border-radius: 10px;
                font-size: 14px;
                font-weight: bold;
            }
        """)
        self.negative_indicator = QLabel("-")
        self.negative_indicator.setFixedSize(20, 20)
        self.negative_indicator.setAlignment(Qt.AlignCenter)
        self.negative_indicator.setStyleSheet("""
            QLabel {
                background-color: #CCCCCC;
                border: 1px solid #333;
                border-radius: 10px;
                font-size: 14px;
                font-weight: bold;
            }
        """)
        polarity_layout.addWidget(self.positive_indicator)
        polarity_layout.addWidget(self.negative_indicator)
        channel_layout.addLayout(polarity_layout)

        # Power ON indicator (default to OFF)
        self.power_indicator = QLabel("OFF")
        self.power_indicator.setFixedSize(40, 25)
        self.power_indicator.setAlignment(Qt.AlignCenter)
        self.power_indicator.setStyleSheet("""
            QLabel {
                background-color: #CCCCCC;
                color: black;
                border: 1px solid #333;
                border-radius: 3px;
                font-weight: bold;
                font-size: 14px;
            }
        """)
        channel_layout.addWidget(self.power_indicator)

        layout.addLayout(channel_layout)

        # Voltage and Current displays (side by side)
        display_layout = QHBoxLayout()

        # Voltage display
        voltage_container = QVBoxLayout()
        voltage_label = QLabel("Voltage (V)")
        voltage_label.setAlignment(Qt.AlignCenter)
        voltage_label.setFont(QFont("Arial", 18))
        voltage_container.addWidget(voltage_label)
        self.voltage_display = QLCDNumber()
        self.voltage_display.setDigitCount(6)
        self.voltage_display.setSegmentStyle(QLCDNumber.Flat)
        self.voltage_display.setStyleSheet("""
            QLCDNumber {
                background-color: #000000;
                color: #FF0000;
                border: 2px solid #333;
            }
        """)
        self.voltage_display.display("000.0")
        voltage_container.addWidget(self.voltage_display)
        display_layout.addLayout(voltage_container)

        # Current display
        current_container = QVBoxLayout()
        current_label = QLabel("Current (μA)")
        current_label.setAlignment(Qt.AlignCenter)
        current_label.setFont(QFont("Arial", 18))
        current_container.addWidget(current_label)
        self.current_display = QLCDNumber()
        self.current_display.setDigitCount(6)
        self.current_display.setSegmentStyle(QLCDNumber.Flat)
        self.current_display.setStyleSheet("""
            QLCDNumber {
                background-color: #000000;
                color: #FF0000;
                border: 2px solid #333;
            }
        """)
        self.current_display.display("0.000")
        current_container.addWidget(self.current_display)
        display_layout.addLayout(current_container)

        layout.addLayout(display_layout)

        # Value input and control buttons
        control_layout = QVBoxLayout()

        # Voltage preset input
        voltage_preset_layout = QHBoxLayout()
        voltage_preset_layout.addWidget(QLabel("Preset V:"))
        self.voltage_preset_input = QDoubleSpinBox()
        self.voltage_preset_input.setRange(0, 800)  # 0-800V
        self.voltage_preset_input.setSuffix(" V")
        self.voltage_preset_input.setSingleStep(0.1)
        voltage_preset_layout.addWidget(self.voltage_preset_input)
        self.set_voltage_preset_btn = QPushButton("Set")
        self.set_voltage_preset_btn.setFixedSize(60, 25)
        self.set_voltage_preset_btn.clicked.connect(self.set_voltage_preset)
        voltage_preset_layout.addWidget(self.set_voltage_preset_btn)
        control_layout.addLayout(voltage_preset_layout)

        # Voltage limit input
        voltage_limit_layout = QHBoxLayout()
        voltage_limit_layout.addWidget(QLabel("Limit V:"))
        self.voltage_limit_input = QDoubleSpinBox()
        self.voltage_limit_input.setRange(0, 800)  # 0-800V
        self.voltage_limit_input.setSuffix(" V")
        self.voltage_limit_input.setSingleStep(0.1)
        voltage_limit_layout.addWidget(self.voltage_limit_input)
        self.set_voltage_limit_btn = QPushButton("Set")
        self.set_voltage_limit_btn.setFixedSize(60, 25)
        self.set_voltage_limit_btn.clicked.connect(self.set_voltage_limit)
        voltage_limit_layout.addWidget(self.set_voltage_limit_btn)
        control_layout.addLayout(voltage_limit_layout)

        # Current limit input
        current_limit_layout = QHBoxLayout()
        current_limit_layout.addWidget(QLabel("Limit I:"))
        self.current_limit_input = QDoubleSpinBox()
        self.current_limit_input.setSingleStep(0.1)
        self.current_limit_input.setDecimals(3)
        self.current_limit_input.setRange(0, 20000)  # 0-20 uA in nA
        self.current_limit_input.setSuffix(" μA")
        current_limit_layout.addWidget(self.current_limit_input)
        self.set_current_limit_btn = QPushButton("Set")
        self.set_current_limit_btn.setFixedSize(60, 25)
        self.set_current_limit_btn.clicked.connect(self.set_current_limit)
        current_limit_layout.addWidget(self.set_current_limit_btn)
        control_layout.addLayout(current_limit_layout)

        # Polarity selection (dropdown)
        polarity_select_layout = QHBoxLayout()
        polarity_select_layout.addWidget(QLabel("Polarity:"))
        self.polarity_combo = QComboBox()
        self.polarity_combo.addItems(["+", "-"])
        self.polarity_combo.setCurrentIndex(0)  # Default to positive
        self.polarity_combo.currentIndexChanged.connect(self._on_polarity_changed)
        polarity_select_layout.addWidget(self.polarity_combo)
        polarity_select_layout.addStretch()
        control_layout.addLayout(polarity_select_layout)

        # Auto shutdown checkbox
        auto_shutdown_layout = QHBoxLayout()
        self.auto_shutdown_checkbox = QCheckBox("Auto Shutdown")
        self.auto_shutdown_checkbox.stateChanged.connect(self._on_auto_shutdown_changed)
        auto_shutdown_layout.addWidget(self.auto_shutdown_checkbox)
        auto_shutdown_layout.addStretch()
        control_layout.addLayout(auto_shutdown_layout)

        # Power control buttons
        power_layout = QHBoxLayout()
        self.on_btn = QPushButton("ON")
        self.on_btn.setStyleSheet("""
            QPushButton {
                background-color: #90EE90;
                font-weight: bold;
            }
        """)
        self.on_btn.clicked.connect(lambda: self.toggle_power(True))
        self.off_btn = QPushButton("OFF")
        self.off_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFCCCC;
                font-weight: bold;
            }
        """)
        self.off_btn.clicked.connect(lambda: self.toggle_power(False))
        power_layout.addWidget(self.on_btn)
        power_layout.addWidget(self.off_btn)
        control_layout.addLayout(power_layout)

        # Temperature compensation settings
        temp_comp_layout = QVBoxLayout()
        temp_comp_group = QGroupBox("Temperature Compensation")
        temp_comp_group_layout = QVBoxLayout()

        # NTC channel selection
        ntc_layout = QHBoxLayout()
        ntc_layout.addWidget(QLabel("NTC:"))
        self.ntc_combo = QComboBox()
        self.ntc_combo.addItems(["Off", "NTC0", "NTC1", "NTC2", "NTC3"])
        self.ntc_combo.currentIndexChanged.connect(self._on_ntc_changed)
        ntc_layout.addWidget(self.ntc_combo)
        temp_comp_group_layout.addLayout(ntc_layout)

        # Reference temperature
        ref_temp_layout = QHBoxLayout()
        ref_temp_layout.addWidget(QLabel("Ref Temp:"))
        self.ref_temp_spin = QDoubleSpinBox()
        self.ref_temp_spin.setRange(-50.0, 150.0)  # -50°C to 150°C in 0.1°C units
        self.ref_temp_spin.setValue(28.5)  # Default 28.5°C
        self.ref_temp_spin.setSuffix(" (0.1°C)")
        self.ref_temp_spin.setSingleStep(0.1)
        self.ref_temp_spin.valueChanged.connect(self._on_ref_temp_changed)
        ref_temp_layout.addWidget(self.ref_temp_spin)
        temp_comp_group_layout.addLayout(ref_temp_layout)

        # Temperature slope
        slope_layout = QHBoxLayout()
        slope_layout.addWidget(QLabel("Slope:"))
        self.slope_spin = QSpinBox()
        self.slope_spin.setRange(-10000, 10000)  # -10V/°C to 10V/°C in mV/°C
        self.slope_spin.setValue(800)  # Default 0.8V/°C
        self.slope_spin.setSuffix(" (mV/°C)")
        self.slope_spin.valueChanged.connect(self._on_slope_changed)
        slope_layout.addWidget(self.slope_spin)
        temp_comp_group_layout.addLayout(slope_layout)

        temp_comp_group.setLayout(temp_comp_group_layout)
        temp_comp_layout.addWidget(temp_comp_group)
        control_layout.addLayout(temp_comp_layout)

        layout.addLayout(control_layout)
        self.setLayout(layout)

    def toggle_power(self, on: bool):
        """Turn channel on or off"""
        if not self.controller.is_connected:
            QMessageBox.warning(self, "Warning", "Device is not connected.")
            return

        try:
            if on:
                self.controller.turn_on(self.channel_num)
                self.power_indicator.setText("ON")
                self.power_indicator.setStyleSheet("""
                    QLabel {
                        background-color: #FF0000;
                        color: white;
                        border: 1px solid #333;
                        border-radius: 3px;
                        font-weight: bold;
                    }
                """)
            else:
                self.controller.turn_off(self.channel_num)
                self.power_indicator.setText("OFF")
                self.power_indicator.setStyleSheet("""
                    QLabel {
                        background-color: #CCCCCC;
                        color: black;
                        border: 1px solid #333;
                        border-radius: 3px;
                        font-weight: bold;
                    }
                """)
        except MHV4Error as e:
            QMessageBox.critical(self, "Error", f"Failed to toggle power:\n{str(e)}")

    def set_voltage_preset(self):
        """Set voltage preset value"""
        if not self.controller.is_connected:
            QMessageBox.warning(self, "Warning", "Device is not connected.")
            return

        try:
            value = self.voltage_preset_input.value()
            # Convert V to 0.1V units
            value_01v = int(value * 10)
            self.controller.set_voltage(self.channel_num, value_01v)
        except MHV4Error as e:
            QMessageBox.critical(self, "Error", f"Failed to set voltage preset:\n{str(e)}")

    def set_voltage_limit(self):
        """Set voltage limit value"""
        if not self.controller.is_connected:
            QMessageBox.warning(self, "Warning", "Device is not connected.")
            return

        try:
            value = self.voltage_limit_input.value()
            # Convert V to 0.1V units
            value_01v = int(value * 10)
            self.controller.set_voltage_limit(self.channel_num, value_01v)
        except MHV4Error as e:
            QMessageBox.critical(self, "Error", f"Failed to set voltage limit:\n{str(e)}")

    def set_current_limit(self):
        """Set current limit value"""
        if not self.controller.is_connected:
            QMessageBox.warning(self, "Warning", "Device is not connected.")
            return

        try:
            value = self.current_limit_input.value()
            value_na = int(value * 1000)
            self.controller.set_current_limit(self.channel_num, value_na)

        except MHV4Error as e:
            QMessageBox.critical(self, "Error", f"Failed to set current limit:\n{str(e)}")

    def _on_polarity_changed(self, index: int):
        """Handle polarity dropdown change"""
        polarity = 'p' if index == 0 else 'n'
        self.set_polarity(polarity)

    def _on_auto_shutdown_changed(self, state: int):
        """Handle auto shutdown checkbox change"""
        enable = (state == Qt.Checked)
        if not self.controller.is_connected:
            QMessageBox.warning(self, "Warning", "Device is not connected.")
            self.auto_shutdown_checkbox.setChecked(not enable)  # Revert
            return

        try:
            self.controller.set_auto_shutdown(self.channel_num, enable)
        except MHV4Error as e:
            QMessageBox.critical(self, "Error", f"Failed to set auto shutdown:\n{str(e)}")
            self.auto_shutdown_checkbox.setChecked(not enable)  # Revert

    def _on_ntc_changed(self, index: int):
        """Handle NTC channel selection change"""
        if not self.controller.is_connected:
            # Temporarily disconnect signal to avoid recursive calls during initialization
            self.ntc_combo.blockSignals(True)
            self.ntc_combo.setCurrentIndex(0)
            self.ntc_combo.blockSignals(False)
            return

        ntc_channel = index - 1  # -1 means Off
        try:
            if ntc_channel < 0:
                self.controller.set_temperature_compensation(self.channel_num, None)
            else:
                self.controller.set_temperature_compensation(self.channel_num, ntc_channel)
        except MHV4Error as e:
            QMessageBox.critical(self, "Error", f"Failed to set NTC channel:\n{str(e)}")
            # Revert on error
            self.ntc_combo.blockSignals(True)
            self.ntc_combo.setCurrentIndex(0)
            self.ntc_combo.blockSignals(False)

    def _on_ref_temp_changed(self, value: float):
        """Handle reference temperature change"""
        if not self.controller.is_connected:
            # Temporarily disconnect signal to avoid recursive calls during initialization
            self.ref_temp_spin.blockSignals(True)
            self.ref_temp_spin.setValue(285)
            self.ref_temp_spin.blockSignals(False)
            return

        try:
            value_01c = int(value * 10)
            self.controller.set_reference_temperature(self.channel_num, value_01c)
        except MHV4Error as e:
            QMessageBox.critical(self, "Error", f"Failed to set reference temperature:\n{str(e)}")
            # Revert on error
            self.ref_temp_spin.blockSignals(True)
            self.ref_temp_spin.setValue(285)
            self.ref_temp_spin.blockSignals(False)

    def _on_slope_changed(self, value: int):
        """Handle temperature slope change"""
        if not self.controller.is_connected:
            # Temporarily disconnect signal to avoid recursive calls during initialization
            self.slope_spin.blockSignals(True)
            self.slope_spin.setValue(800)
            self.slope_spin.blockSignals(False)
            return

        try:
            self.controller.set_temperature_slope(self.channel_num, value)
        except MHV4Error as e:
            QMessageBox.critical(self, "Error", f"Failed to set temperature slope:\n{str(e)}")
            # Revert on error
            self.slope_spin.blockSignals(True)
            self.slope_spin.setValue(800)
            self.slope_spin.blockSignals(False)

    def set_polarity(self, polarity: str):
        """Set polarity (positive or negative)"""
        if not self.controller.is_connected:
            QMessageBox.warning(self, "Warning", "Device is not connected.")
            return

        try:
            self.controller.set_polarity(self.channel_num, polarity)
            # Block signals to avoid recursive calls when updating combo
            self.polarity_combo.blockSignals(True)
            if polarity.lower() in ['p', '+', '1']:
                # Update indicators
                self.positive_indicator.setStyleSheet("""
                    QLabel {
                        background-color: #90EE90;
                        border: 1px solid #333;
                        border-radius: 10px;
                    }
                """)
                self.negative_indicator.setStyleSheet("""
                    QLabel {
                        background-color: #CCCCCC;
                        border: 1px solid #333;
                        border-radius: 10px;
                    }
                """)
                # Update dropdown
                self.polarity_combo.setCurrentIndex(0)
            else:
                # Update indicators
                self.positive_indicator.setStyleSheet("""
                    QLabel {
                        background-color: #CCCCCC;
                        border: 1px solid #333;
                        border-radius: 10px;
                    }
                """)
                self.negative_indicator.setStyleSheet("""
                    QLabel {
                        background-color: #90EE90;
                        border: 1px solid #333;
                        border-radius: 10px;
                    }
                """)
                # Update dropdown
                self.polarity_combo.setCurrentIndex(1)
            self.polarity_combo.blockSignals(False)

        except MHV4Error as e:
            self.polarity_combo.blockSignals(False)
            QMessageBox.critical(self, "Error", f"Failed to set polarity:\n{str(e)}")

    def update_readings(self):
        """Update voltage and current readings"""
        if not self.controller.is_connected:
            return

        try:
            # Update voltage
            voltage_response = self.controller.read_voltage(self.channel_num)
            if voltage_response:
                try:
                    # Try to parse response - device may return format like "RU 0 1234" or just "1234"
                    parts = voltage_response.strip().split()
                    for part in reversed(parts):
                        try:
                            value = float(part)
                            # Convert from 0.1V units if needed (values > 8000 would be invalid in V)
                            if value > 8000:  # Likely in 0.1V units (800V * 10 = 8000)
                                value = value / 10.0
                            elif value > 800:  # Still might be in 0.1V units
                                value = value / 10.0
                            # Ensure value is within valid range
                            if -800 <= value <= 800:
                                self.voltage_display.display(f"{value:.1f}")
                            break
                        except ValueError:
                            continue
                except Exception as e:
                    # Silently continue if parsing fails
                    pass

            # Update current
            current_response = self.controller.read_current(self.channel_num)
            if current_response:
                try:
                    # Try to parse response - device may return format like "RI 0 12345" or just "12345"
                    parts = current_response.strip().split()
                    for part in reversed(parts):
                        try:
                            value = float(part)
                            # Device returns current in nA, convert to μA for display
                            # If value is very small (< 1), might already be in μA
                            if value > 1000:  # Likely in nA, convert to μA
                                value = value / 1000.0
                            elif value > 100:  # Probably in nA
                                value = value / 1000.0
                            # Display in μA
                            self.current_display.display(f"{value:.3f}")
                            break
                        except ValueError:
                            continue
                except Exception as e:
                    # Silently continue if parsing fails
                    pass
        except MHV4Error:
            pass
        except Exception:
            # Ignore any other errors during update
            pass

    def load_initial_values(self):
        """Load all initial values from device"""
        if not self.controller.is_connected:
            return

        try:
            # Load voltage preset
            try:
                response = self.controller.read_voltage_preset(self.channel_num)
                value = self._parse_value(response)
                if value is not None:
                    self.voltage_preset_input.blockSignals(True)
                    self.voltage_preset_input.setValue(abs(value))
                    self.voltage_preset_input.blockSignals(False)
            except Exception as e:
                # Silently continue if loading fails
                pass

            # Load voltage limit
            try:
                response = self.controller.read_voltage_limit(self.channel_num)
                value = self._parse_value(response)
                if value is not None:
                    self.voltage_limit_input.blockSignals(True)
                    self.voltage_limit_input.setValue(abs(value))
                    self.voltage_limit_input.blockSignals(False)
            except Exception as e:
                # Silently continue if loading fails
                pass

            # Load current limit
            try:
                response = self.controller.read_current_limit(self.channel_num)
                value = self._parse_value(response)
                if value is not None:
                    # Device returns value in nA units
                    self.current_limit_input.blockSignals(True)
                    self.current_limit_input.setValue(abs(value))
                    self.current_limit_input.blockSignals(False)
            except Exception as e:
                # Silently continue if loading fails
                pass

            # Load polarity
            try:
                response = self.controller.read_polarity(self.channel_num)
                polarity = response.split()[-1].strip().lower()
                # Block signals to avoid triggering commands during load
                self.polarity_combo.blockSignals(True)
                if polarity == 'positive':
                    self.positive_indicator.setStyleSheet("""
                        QLabel {
                            background-color: #90EE90;
                            border: 1px solid #333;
                            border-radius: 10px;
                        }
                    """)
                    self.negative_indicator.setStyleSheet("""
                        QLabel {
                            background-color: #CCCCCC;
                            border: 1px solid #333;
                            border-radius: 10px;
                        }
                    """)
                    self.polarity_combo.setCurrentIndex(0)
                elif polarity == 'negative':
                    self.positive_indicator.setStyleSheet("""
                        QLabel {
                            background-color: #CCCCCC;
                            border: 1px solid #333;
                            border-radius: 10px;
                        }
                    """)
                    self.negative_indicator.setStyleSheet("""
                        QLabel {
                            background-color: #90EE90;
                            border: 1px solid #333;
                            border-radius: 10px;
                        }
                    """)
                    self.polarity_combo.setCurrentIndex(1)
                self.polarity_combo.blockSignals(False)
            except:
                pass

            # Load auto shutdown (would need read command if available)
            # For now, we'll assume it's disabled by default

            # Load temperature compensation
            try:
                response = self.controller.read_temperature_compensation(self.channel_num)
                # Parse NTC channel from response
                self.ntc_combo.blockSignals(True)
                parts = response.split()
                found = False
                for part in parts:
                    if part.lower() in ['off', '-', '4']:
                        self.ntc_combo.setCurrentIndex(0)  # Off
                        found = True
                        break
                    try:
                        ntc_num = int(part)
                        if 0 <= ntc_num <= 3:
                            self.ntc_combo.setCurrentIndex(ntc_num + 1)  # NTC0 = index 1
                            found = True
                            break
                    except ValueError:
                        continue
                if not found:
                    self.ntc_combo.setCurrentIndex(0)  # Default to Off
                self.ntc_combo.blockSignals(False)
            except:
                pass

            # Load reference temperature
            try:
                # Would need read command if available
                # For now, keep default value
                pass
            except:
                pass

            # Load temperature slope
            try:
                # Would need read command if available
                # For now, keep default value
                pass
            except:
                pass

            # Ramp speed is now handled at module level, not channel level
            # All channels start as OFF regardless of voltage
            # (Remove automatic ON detection)

        except MHV4Error:
            pass

    def _parse_value(self, response: str) -> Optional[float]:
        """Parse numeric value from response string

        Device responses typically contain the command echo and the value.
        We search for the first valid numeric value from the end.
        """
        if not response or not response.strip():
            return None

        try:
            parts = response.strip().split()
            # Search from the end (value is usually at the end of response)
            for part in reversed(parts):
                cleaned = part.strip()
                try:
                    value = float(cleaned)
                    # Allow both positive and negative values
                    return value
                except ValueError:
                    continue
        except Exception:
            pass
        return None



class ModulePanel(QWidget):
    """Complete module control panel (4 channels)"""

    def __init__(self, controller: MHV4Controller):
        super().__init__()
        self.controller = controller
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_all_readings)
        self.init_ui()

    def init_ui(self):
        """Initialize module panel UI"""
        layout = QVBoxLayout()
        layout.setSpacing(5)
        layout.setContentsMargins(5, 5, 5, 5)

        # Module header
        header_layout = QHBoxLayout()
        header_label = QLabel("MHV-4 - 4 Channel 800V High Voltage Supply")
        header_label.setFont(QFont("Arial", 14, QFont.Bold))
        header_layout.addWidget(header_label)
        header_layout.addStretch()

        # Ramp speed control (global for all channels)
        ramp_speed_layout = QHBoxLayout()
        ramp_speed_layout.addWidget(QLabel("Ramp Speed:"))
        self.ramp_speed_combo = QComboBox()
        self.ramp_speed_combo.addItems(["5 V/s", "25 V/s", "100 V/s", "500 V/s"])
        self.ramp_speed_combo.setCurrentIndex(1)  # Default to 25 V/s
        self.ramp_speed_combo.currentIndexChanged.connect(self._on_ramp_speed_changed)
        ramp_speed_layout.addWidget(self.ramp_speed_combo)
        header_layout.addLayout(ramp_speed_layout)

        layout.addLayout(header_layout)

        # Channel panels (4 channels in a grid)
        channels_layout = QGridLayout()
        self.channel_panels = []
        for ch in range(4):
            panel = ChannelPanel(ch, self.controller)
            self.channel_panels.append(panel)
            channels_layout.addWidget(panel, 0, ch)
        layout.addLayout(channels_layout)

        # Timer will be started when module is connected
        # Don't start here as controller might not be connected yet

        self.setLayout(layout)

    def _on_ramp_speed_changed(self, index: int):
        """Handle ramp speed dropdown change"""
        if not self.controller.is_connected:
            # Temporarily disconnect signal to avoid recursive calls during initialization
            self.ramp_speed_combo.blockSignals(True)
            self.ramp_speed_combo.setCurrentIndex(1)  # Default to 25 V/s
            self.ramp_speed_combo.blockSignals(False)
            return

        try:
            self.controller.set_ramp_speed(index)
        except MHV4Error as e:
            QMessageBox.critical(self, "Error", f"Failed to set ramp speed:\n{str(e)}")
            # Revert on error
            self.ramp_speed_combo.blockSignals(True)
            self.ramp_speed_combo.setCurrentIndex(1)  # Default to 25 V/s
            self.ramp_speed_combo.blockSignals(False)

    def load_all_initial_values(self):
        """Load all initial values for all channels"""
        if not self.controller.is_connected:
            return

        # Load initial values for each channel
        for panel in self.channel_panels:
            panel.load_initial_values()

        # Load ramp speed
        try:
            response = self.controller.read_ramp_speed()
            print(response)
            if response:
                # Parse ramp speed index from response
                # Format might be like "RRA 1" or just "1" where 1 is the index
                ramp_speed = int(response.split()[-2])
                ramp_speed_dict = {5: 0, 25: 1, 100: 2, 500: 3}
                self.ramp_speed_combo.blockSignals(True)
                self.ramp_speed_combo.setCurrentIndex(ramp_speed_dict[ramp_speed])
                self.ramp_speed_combo.blockSignals(False)
        except Exception as e:
            pass
        except MHV4Error as e:
            pass

    def update_all_readings(self):
        """Update all channel readings"""
        if self.controller.is_connected:
            for panel in self.channel_panels:
                panel.update_readings()

    def start_updates(self):
        """Start periodic updates"""
        if self.controller.is_connected:
            # Start timer with 1 second interval
            if not self.update_timer.isActive():
                self.update_timer.start(1000)
            # Load initial values when connected
            self.load_all_initial_values()

    def stop_updates(self):
        """Stop periodic updates"""
        self.update_timer.stop()


class ConnectionPanel(QGroupBox):
    """Connection settings panel"""

    connection_changed = pyqtSignal(bool, object)  # (connected, controller)

    def __init__(self):
        super().__init__("Connection Settings")
        self.controller = None
        self.is_connected = False
        self.init_ui()
        self.refresh_ports()

    def init_ui(self):
        """Initialize connection panel UI"""
        layout = QGridLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # Port selection
        layout.addWidget(QLabel("Port:"), 0, 0)
        self.port_combo = QComboBox()
        self.port_combo.setMinimumWidth(200)
        layout.addWidget(self.port_combo, 0, 1)

        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.refresh_ports)
        layout.addWidget(self.refresh_btn, 0, 2)

        # Connection button
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self.toggle_connection)
        layout.addWidget(self.connect_btn, 0, 3)

        # Connection status
        self.status_label = QLabel("Not Connected")
        self.status_label.setStyleSheet("color: red; font-weight: bold;")
        layout.addWidget(self.status_label, 0, 4)

        self.setLayout(layout)

    def refresh_ports(self):
        """Refresh available serial ports"""
        self.port_combo.clear()
        ports = serial.tools.list_ports.comports()
        if ports:
            for port in ports:
                self.port_combo.addItem(f"{port.device} - {port.description}")
        else:
            self.port_combo.addItem("No available ports")

    def toggle_connection(self):
        """Toggle connection/disconnection"""
        if self.is_connected:
            self.disconnect_device()
        else:
            self.connect_device()

    def connect_device(self):
        """Connect to device"""
        try:
            port_text = self.port_combo.currentText()
            if "No available ports" in port_text:
                QMessageBox.warning(self, "Warning", "No available ports found.")
                return

            port = port_text.split(" - ")[0]
            self.controller = MHV4Controller(port=port, baudrate=9600)
            self.controller.connect()

            self.is_connected = True
            self.update_ui()
            self.connection_changed.emit(True, self.controller)

        except MHV4Error as e:
            QMessageBox.critical(self, "Connection Error", f"Failed to connect:\n{str(e)}")

    def disconnect_device(self):
        """Disconnect from device"""
        try:
            if self.controller:
                self.controller.disconnect()
                self.controller = None

            self.is_connected = False
            self.update_ui()
            self.connection_changed.emit(False, None)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error during disconnection:\n{str(e)}")

    def update_ui(self):
        """Update UI state"""
        if self.is_connected:
            self.connect_btn.setText("Disconnect")
            self.status_label.setText("Connected")
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
            self.port_combo.setEnabled(False)
        else:
            self.connect_btn.setText("Connect")
            self.status_label.setText("Not Connected")
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
            self.port_combo.setEnabled(True)


class MHV4MainWindow(QMainWindow):
    """Main window for MHV-4 GUI application"""

    def __init__(self, auto_connect_port=None):
        super().__init__()
        self.modules = {}  # {module_name: (controller, panel)}
        self.auto_connect_port = auto_connect_port
        self.init_ui()
        # Auto-connect if port is provided
        if auto_connect_port:
            QTimer.singleShot(100, self.auto_connect_device)

    def init_ui(self):
        """Initialize main window UI"""
        self.setWindowTitle("MHV-4 NIM Device Controller")
        self.setGeometry(100, 100, 1400, 900)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)

        # Module management section
        module_mgmt_layout = QHBoxLayout()
        module_mgmt_layout.addWidget(QLabel("Modules:"))

        self.add_module_btn = QPushButton("Add Module")
        self.add_module_btn.clicked.connect(self.add_module)
        module_mgmt_layout.addWidget(self.add_module_btn)

        self.remove_module_btn = QPushButton("Remove Module")
        self.remove_module_btn.clicked.connect(self.remove_module)
        module_mgmt_layout.addWidget(self.remove_module_btn)

        module_mgmt_layout.addStretch()
        main_layout.addLayout(module_mgmt_layout)

        # Tab widget for multiple modules
        self.tab_widget = QTabWidget()
        self.tab_widget.setContentsMargins(0, 0, 0, 0)
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                margin: 0px;
                padding: 0px;
                border: 1px solid #C0C0C0;
                top: -1px;
            }
        """)
        main_layout.addWidget(self.tab_widget)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

        central_widget.setLayout(main_layout)

    def add_module(self):
        """Add a new module"""
        # Create connection panel dialog
        dialog = QWidget()
        dialog.setWindowTitle("Add Module")
        dialog.setGeometry(200, 200, 500, 200)

        layout = QVBoxLayout()

        conn_panel = ConnectionPanel()
        conn_panel.connection_changed.connect(lambda connected, ctrl:
                                             self.on_module_connected(connected, ctrl, dialog))
        layout.addWidget(conn_panel)

        dialog.setLayout(layout)
        dialog.show()

    def on_module_connected(self, connected: bool, controller, dialog=None):
        """Handle module connection"""
        if connected and controller:
            module_name = f"Module {len(self.modules) + 1}"
            panel = ModulePanel(controller)
            self.tab_widget.addTab(panel, module_name)
            self.modules[module_name] = (controller, panel)
            panel.start_updates()
            # Initial values are already loaded in ModulePanel.__init__
            if dialog:
                dialog.close()
            self.status_bar.showMessage(f"{module_name} connected. Initial values loaded.")
            return True
        return False

    def auto_connect_device(self):
        """Auto-connect to device using provided port"""
        if not self.auto_connect_port:
            return

        try:
            controller = MHV4Controller(port=self.auto_connect_port, baudrate=9600)
            controller.connect()

            if controller.is_connected:
                # Add module without dialog
                self.on_module_connected(True, controller, None)
                self.status_bar.showMessage(f"Auto-connected to {self.auto_connect_port}")
            else:
                QMessageBox.warning(self, "Connection Failed",
                                 f"Failed to connect to {self.auto_connect_port}")
        except MHV4Error as e:
            QMessageBox.critical(self, "Connection Error",
                               f"Failed to auto-connect to {self.auto_connect_port}:\n{str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Error",
                               f"Unexpected error during auto-connect:\n{str(e)}")

    def remove_module(self):
        """Remove current module"""
        current_index = self.tab_widget.currentIndex()
        if current_index >= 0:
            module_name = self.tab_widget.tabText(current_index)
            reply = QMessageBox.question(self, 'Remove Module',
                                       f'Remove {module_name}?',
                                       QMessageBox.Yes | QMessageBox.No,
                                       QMessageBox.No)
            if reply == QMessageBox.Yes:
                controller, panel = self.modules[module_name]
                panel.stop_updates()
                if controller.is_connected:
                    controller.disconnect()
                self.tab_widget.removeTab(current_index)
                del self.modules[module_name]
                self.status_bar.showMessage(f"{module_name} removed.")

    def closeEvent(self, event):
        """Handle window close event"""
        for module_name, (controller, panel) in self.modules.items():
            panel.stop_updates()
            if controller.is_connected:
                reply = QMessageBox.question(self, 'Exit Confirmation',
                                           f'{module_name} is connected. Disconnect?',
                                           QMessageBox.Yes | QMessageBox.No,
                                           QMessageBox.No)
                if reply == QMessageBox.Yes:
                    controller.disconnect()
                else:
                    event.ignore()
                    return
        event.accept()


def main():
    """Main function"""
    app = QApplication(sys.argv)

    # Set application information
    app.setApplicationName("MHV-4 Controller")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("MHV-4")

    # Parse command line arguments for auto-connect
    auto_connect_port = None
    if len(sys.argv) > 1:
        auto_connect_port = sys.argv[1]
        print(f"Auto-connecting to device at: {auto_connect_port}")

    # Create and show main window
    window = MHV4MainWindow(auto_connect_port=auto_connect_port)
    window.show()

    # Start event loop
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

