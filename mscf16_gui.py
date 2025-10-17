"""
MSCF-16 NIM Device GUI Application

PyQt5 기반의 MSCF-16 장치 제어 GUI 애플리케이션
"""

import sys
import serial.tools.list_ports
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                            QHBoxLayout, QTabWidget, QLabel, QPushButton,
                            QComboBox, QSpinBox, QCheckBox, QGroupBox,
                            QTextEdit, QStatusBar, QMessageBox, QGridLayout,
                            QSlider, QProgressBar, QSplitter)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QIcon
from mscf16_controller import MSCF16Controller, MSCF16Error
from mscf16_constants import Parameters


class ConnectionPanel(QGroupBox):
    """Connection Settings Panel"""

    connection_changed = pyqtSignal(bool)  # Connection status change signal

    def __init__(self):
        super().__init__("Connection Settings")
        self.controller = None
        self.is_connected = False
        self.init_ui()
        self.refresh_ports()

    def init_ui(self):
        layout = QGridLayout()

        # Port selection
        layout.addWidget(QLabel("Port:"), 0, 0)
        self.port_combo = QComboBox()
        self.port_combo.setMinimumWidth(200)
        layout.addWidget(self.port_combo, 0, 1)

        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.refresh_ports)
        layout.addWidget(self.refresh_btn, 0, 2)

        # Baud rate selection
        layout.addWidget(QLabel("Baud Rate:"), 0, 3)
        self.baudrate_combo = QComboBox()
        self.baudrate_combo.addItems(["9600", "19200", "28400", "57600", "115200"])
        self.baudrate_combo.setCurrentText("9600")
        layout.addWidget(self.baudrate_combo, 0, 4)

        # Connection button
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self.toggle_connection)
        layout.addWidget(self.connect_btn, 0, 5)

        # Connection status display
        self.status_label = QLabel("Not Connected")
        self.status_label.setStyleSheet("color: red; font-weight: bold;")
        layout.addWidget(self.status_label, 0, 6)

        self.setLayout(layout)

    def refresh_ports(self):
        """Refresh list of available serial ports"""
        self.port_combo.clear()
        ports = serial.tools.list_ports.comports()

        if ports:
            for port in ports:
                self.port_combo.addItem(f"{port.device} - {port.description}")
        else:
            self.port_combo.addItem("No available ports")

    def toggle_connection(self):
        """Toggle connection/disconnection"""
        if not self.is_connected:
            self.connect_device()
        else:
            self.disconnect_device()

    def connect_device(self):
        """Connect to device"""
        try:
            port_text = self.port_combo.currentText()
            if "No available ports" in port_text:
                QMessageBox.warning(self, "Warning", "No available ports found.")
                return

            port = port_text.split(" - ")[0]
            baudrate = int(self.baudrate_combo.currentText())

            self.controller = MSCF16Controller(port=port, baudrate=baudrate)
            self.controller.connect()

            self.is_connected = True
            self.update_ui()
            self.connection_changed.emit(True)

            QMessageBox.information(self, "Success", f"Connected to device.\nPort: {port}\nBaud Rate: {baudrate}")

        except MSCF16Error as e:
            QMessageBox.critical(self, "Connection Error", f"Failed to connect to device:\n{str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Unexpected error occurred:\n{str(e)}")

    def disconnect_device(self):
        """Disconnect from device"""
        try:
            if self.controller:
                self.controller.disconnect()
                self.controller = None

            self.is_connected = False
            self.update_ui()
            self.connection_changed.emit(False)

            QMessageBox.information(self, "Info", "Device disconnected.")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error occurred during disconnection:\n{str(e)}")

    def update_ui(self):
        """Update UI state"""
        if self.is_connected:
            self.connect_btn.setText("Disconnect")
            self.status_label.setText("Connected")
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
            self.port_combo.setEnabled(False)
            self.baudrate_combo.setEnabled(False)
            self.refresh_btn.setEnabled(False)
        else:
            self.connect_btn.setText("Connect")
            self.status_label.setText("Not Connected")
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
            self.port_combo.setEnabled(True)
            self.baudrate_combo.setEnabled(True)
            self.refresh_btn.setEnabled(True)


class CombinedControlPanel(QWidget):
    """Combined Channel and Group Control Panel"""

    def __init__(self, connection_panel):
        super().__init__()
        self.connection_panel = connection_panel
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Create vertical splitter for top-bottom layout
        splitter = QSplitter(Qt.Vertical)

        # Top side: Channel Control
        channel_widget = QWidget()
        channel_layout = QVBoxLayout()

        # Threshold settings
        threshold_group = QGroupBox("Threshold Settings")
        threshold_layout = QVBoxLayout()

        # Individual channel Threshold settings
        individual_threshold_layout = QVBoxLayout()

        # Channel Threshold value input (2 rows)
        self.threshold_spins = {}
        for row in range(2):
            row_layout = QHBoxLayout()
            for col in range(8):
                channel_num = row * 8 + col + 1

                # Channel number label
                channel_label = QLabel(f"CH{channel_num}")
                channel_label.setFixedWidth(35)
                row_layout.addWidget(channel_label)

                # Threshold value input
                spin_box = QSpinBox()
                spin_box.setRange(0, 255)
                spin_box.setValue(128)
                spin_box.setFixedWidth(50)
                self.threshold_spins[channel_num] = spin_box
                row_layout.addWidget(spin_box)

                # Set button
                btn = QPushButton("Set")
                btn.setFixedSize(50, 25)
                btn.clicked.connect(lambda checked, ch=channel_num: self.set_threshold(ch))
                row_layout.addWidget(btn)

                row_layout.addSpacing(5)
            individual_threshold_layout.addLayout(row_layout)

        threshold_layout.addLayout(individual_threshold_layout)

        # Common Threshold settings
        common_threshold_layout = QHBoxLayout()
        common_threshold_layout.addWidget(QLabel("Common Threshold:"))
        self.common_threshold_spin = QSpinBox()
        self.common_threshold_spin.setRange(0, 255)
        self.common_threshold_spin.setValue(128)
        self.common_threshold_spin.setFixedWidth(60)
        common_threshold_layout.addWidget(self.common_threshold_spin)

        common_btn = QPushButton("Apply to All Channels")
        common_btn.setFixedSize(150, 30)
        common_btn.setStyleSheet("QPushButton { background-color: #ffcccc; font-weight: bold; }")
        common_btn.clicked.connect(lambda: self.set_threshold(17))
        common_threshold_layout.addWidget(common_btn)
        common_threshold_layout.addStretch()

        threshold_layout.addLayout(common_threshold_layout)
        threshold_group.setLayout(threshold_layout)
        channel_layout.addWidget(threshold_group)

        # PZ value settings
        pz_group = QGroupBox("PZ Value Settings")
        pz_layout = QVBoxLayout()

        # Individual channel PZ settings
        individual_pz_layout = QVBoxLayout()

        # Channel PZ value input (2 rows)
        self.pz_spins = {}
        for row in range(2):
            row_layout = QHBoxLayout()
            for col in range(8):
                channel_num = row * 8 + col + 1

                # Channel number label
                channel_label = QLabel(f"CH{channel_num}")
                channel_label.setFixedWidth(35)
                row_layout.addWidget(channel_label)

                # PZ value input
                spin_box = QSpinBox()
                spin_box.setRange(0, 255)
                spin_box.setValue(100)
                spin_box.setFixedWidth(50)
                self.pz_spins[channel_num] = spin_box
                row_layout.addWidget(spin_box)

                # Set button
                btn = QPushButton("Set")
                btn.setFixedSize(50, 25)
                btn.clicked.connect(lambda checked, ch=channel_num: self.set_pz_value(ch))
                row_layout.addWidget(btn)

                row_layout.addSpacing(5)
            individual_pz_layout.addLayout(row_layout)

        pz_layout.addLayout(individual_pz_layout)

        # Common PZ settings
        common_pz_layout = QHBoxLayout()
        common_pz_layout.addWidget(QLabel("Common PZ Value:"))
        self.common_pz_spin = QSpinBox()
        self.common_pz_spin.setRange(0, 255)
        self.common_pz_spin.setValue(100)
        self.common_pz_spin.setFixedWidth(60)
        common_pz_layout.addWidget(self.common_pz_spin)

        common_pz_btn = QPushButton("Apply to All Channels")
        common_pz_btn.setFixedSize(150, 30)
        common_pz_btn.setStyleSheet("QPushButton { background-color: #ccffcc; font-weight: bold; }")
        common_pz_btn.clicked.connect(lambda: self.set_pz_value(17))
        common_pz_layout.addWidget(common_pz_btn)
        common_pz_layout.addStretch()

        pz_layout.addLayout(common_pz_layout)
        pz_group.setLayout(pz_layout)
        channel_layout.addWidget(pz_group)

        # Monitor channel settings
        monitor_group = QGroupBox("Monitor Channel Settings")
        monitor_layout = QVBoxLayout()

        # Monitor channel buttons (1-16 only)
        monitor_channels_layout = QVBoxLayout()
        for row in range(1):
            row_layout = QHBoxLayout()
            for col in range(16):
                channel_num = row * 16 + col + 1
                btn = QPushButton(f"M{channel_num}")
                btn.setFixedSize(50, 30)
                btn.setStyleSheet("QPushButton { background-color: #ccccff; }")
                btn.clicked.connect(lambda checked, ch=channel_num: self.set_monitor_channel(ch))
                row_layout.addWidget(btn)
            monitor_channels_layout.addLayout(row_layout)

        monitor_layout.addLayout(monitor_channels_layout)
        monitor_group.setLayout(monitor_layout)
        channel_layout.addWidget(monitor_group)

        # Automatic PZ settings
        auto_pz_group = QGroupBox("Automatic PZ Settings")
        auto_pz_layout = QVBoxLayout()

        # Automatic PZ channel buttons (1-16 only)
        auto_pz_channels_layout = QVBoxLayout()
        for row in range(1):
            row_layout = QHBoxLayout()
            for col in range(16):
                channel_num = row * 16 + col + 1
                btn = QPushButton(f"AP{channel_num}")
                btn.setFixedSize(50, 30)
                btn.setStyleSheet("QPushButton { background-color: #ffffcc; }")
                btn.clicked.connect(lambda checked, ch=channel_num: self.set_automatic_pz(ch))
                row_layout.addWidget(btn)
            auto_pz_channels_layout.addLayout(row_layout)

        auto_pz_layout.addLayout(auto_pz_channels_layout)
        auto_pz_group.setLayout(auto_pz_layout)
        channel_layout.addWidget(auto_pz_group)

        channel_widget.setLayout(channel_layout)
        splitter.addWidget(channel_widget)

        # Bottom side: Group Control
        group_widget = QWidget()
        group_layout = QVBoxLayout()

        # Shaping Time settings
        shaping_group = QGroupBox("Shaping Time Settings")

        # Group Shaping Time value input (2x2 grid)
        self.shaping_spins = {}
        row_layout = QHBoxLayout()
        for group_num in range(1, 5):
            # Group number label
            group_label = QLabel(f"G{group_num}:")
            group_label.setFixedWidth(30)
            row_layout.addWidget(group_label)

            spin_box = QSpinBox()
            spin_box.setRange(0, 15)
            spin_box.setValue(8)
            spin_box.setFixedWidth(60)
            self.shaping_spins[group_num] = spin_box
            row_layout.addWidget(spin_box)

            # Set button
            btn = QPushButton("Set")
            btn.setFixedSize(50, 25)
            btn.clicked.connect(lambda checked, g=group_num: self.set_shaping_time(g))
            row_layout.addWidget(btn)

            row_layout.addSpacing(20)

        # Common Shaping Time settings
        row_layout.addWidget(QLabel("Common Shaping Time:"))
        self.common_shaping_spin = QSpinBox()
        self.common_shaping_spin.setRange(0, 15)
        self.common_shaping_spin.setValue(8)
        self.common_shaping_spin.setFixedWidth(60)
        row_layout.addWidget(self.common_shaping_spin)

        common_shaping_btn = QPushButton("Apply to All Groups")
        common_shaping_btn.setFixedSize(150, 30)
        common_shaping_btn.setStyleSheet("QPushButton { background-color: #ffddcc; font-weight: bold; }")
        common_shaping_btn.clicked.connect(lambda: self.set_shaping_time(5))
        row_layout.addWidget(common_shaping_btn)
        #common_shaping_layout.addStretch()

        #individual_shaping_layout.addLayout(common_shaping_layout)
        shaping_group.setLayout(row_layout)
        group_layout.addWidget(shaping_group)

        # Gain settings
        gain_group = QGroupBox("Gain Settings")
        gain_layout = QHBoxLayout()

        # Individual group Gain settings
        # Group Gain value input (2x2 grid)
        self.gain_spins = {}
        for group_num in range(1, 5):
            # Group number label
            group_label = QLabel(f"G{group_num}:")
            group_label.setFixedWidth(30)
            gain_layout.addWidget(group_label)

            # Gain value input
            spin_box = QSpinBox()
            spin_box.setRange(0, 15)
            spin_box.setValue(8)
            spin_box.setFixedWidth(60)
            self.gain_spins[group_num] = spin_box
            gain_layout.addWidget(spin_box)

            # Set button
            btn = QPushButton("Set")
            btn.setFixedSize(50, 25)
            btn.clicked.connect(lambda checked, g=group_num: self.set_gain(g))
            gain_layout.addWidget(btn)

            gain_layout.addSpacing(20)

        # Common Gain settings
        gain_layout.addWidget(QLabel("Common Gain:"))
        self.common_gain_spin = QSpinBox()
        self.common_gain_spin.setRange(0, 15)
        self.common_gain_spin.setValue(8)
        self.common_gain_spin.setFixedWidth(60)
        gain_layout.addWidget(self.common_gain_spin)

        common_gain_btn = QPushButton("Apply to All Groups")
        common_gain_btn.setFixedSize(150, 30)
        common_gain_btn.setStyleSheet("QPushButton { background-color: #ddffdd; font-weight: bold; }")
        common_gain_btn.clicked.connect(lambda: self.set_gain(5))
        gain_layout.addWidget(common_gain_btn)
        #common_gain_layout.addStretch()

        #individual_gain_layout.addLayout(common_gain_layout)
        gain_group.setLayout(gain_layout)
        group_layout.addWidget(gain_group)

        group_widget.setLayout(group_layout)
        splitter.addWidget(group_widget)

        # Set splitter proportions (60% channel, 40% group)
        splitter.setSizes([400, 300])

        layout.addWidget(splitter)
        self.setLayout(layout)

    def set_threshold(self, channel):
        """Set Threshold"""
        if not self.connection_panel.is_connected:
            QMessageBox.warning(self, "Warning", "Device is not connected.")
            return

        try:
            if channel == 17:
                value = self.common_threshold_spin.value()
                self.connection_panel.controller.set_threshold(channel, value)
                QMessageBox.information(self, "Success", f"All channels threshold set to {value}.")
            else:
                value = self.threshold_spins[channel].value()
                self.connection_panel.controller.set_threshold(channel, value)
                QMessageBox.information(self, "Success", f"Channel {channel} threshold set to {value}.")

        except MSCF16Error as e:
            QMessageBox.critical(self, "Error", f"Threshold setting failed:\n{str(e)}")

    def set_pz_value(self, channel):
        """Set PZ Value"""
        if not self.connection_panel.is_connected:
            QMessageBox.warning(self, "Warning", "Device is not connected.")
            return

        try:
            if channel == 17:
                value = self.common_pz_spin.value()
                self.connection_panel.controller.set_pz_value(channel, value)
                QMessageBox.information(self, "Success", f"All channels PZ value set to {value}.")
            else:
                value = self.pz_spins[channel].value()
                self.connection_panel.controller.set_pz_value(channel, value)
                QMessageBox.information(self, "Success", f"Channel {channel} PZ value set to {value}.")

        except MSCF16Error as e:
            QMessageBox.critical(self, "Error", f"PZ value setting failed:\n{str(e)}")

    def set_monitor_channel(self, channel):
        """Set Monitor Channel"""
        if not self.connection_panel.is_connected:
            QMessageBox.warning(self, "Warning", "Device is not connected.")
            return

        try:
            self.connection_panel.controller.set_monitor_channel(channel)
            QMessageBox.information(self, "Success", f"Channel {channel} set as monitor channel.")

        except MSCF16Error as e:
            QMessageBox.critical(self, "Error", f"Monitor channel setting failed:\n{str(e)}")

    def set_automatic_pz(self, channel):
        """Set Automatic PZ"""
        if not self.connection_panel.is_connected:
            QMessageBox.warning(self, "Warning", "Device is not connected.")
            return

        try:
            self.connection_panel.controller.set_automatic_pz(channel)
            QMessageBox.information(self, "Success", f"Automatic PZ set for channel {channel}.")

        except MSCF16Error as e:
            QMessageBox.critical(self, "Error", f"Automatic PZ setting failed:\n{str(e)}")

    def set_shaping_time(self, group):
        """Set Shaping Time"""
        if not self.connection_panel.is_connected:
            QMessageBox.warning(self, "Warning", "Device is not connected.")
            return

        try:
            if group == 5:
                value = self.common_shaping_spin.value()
                self.connection_panel.controller.set_shaping_time(group, value)
                QMessageBox.information(self, "Success", f"All groups shaping time set to {value}.")
            else:
                value = self.shaping_spins[group].value()
                self.connection_panel.controller.set_shaping_time(group, value)
                QMessageBox.information(self, "Success", f"Group {group} shaping time set to {value}.")

        except MSCF16Error as e:
            QMessageBox.critical(self, "Error", f"Shaping time setting failed:\n{str(e)}")

    def set_gain(self, group):
        """Set Gain"""
        if not self.connection_panel.is_connected:
            QMessageBox.warning(self, "Warning", "Device is not connected.")
            return

        try:
            if group == 5:
                value = self.common_gain_spin.value()
                self.connection_panel.controller.set_gain(group, value)
                QMessageBox.information(self, "Success", f"All groups gain set to {value}.")
            else:
                value = self.gain_spins[group].value()
                self.connection_panel.controller.set_gain(group, value)
                QMessageBox.information(self, "Success", f"Group {group} gain set to {value}.")

        except MSCF16Error as e:
            QMessageBox.critical(self, "Error", f"Gain setting failed:\n{str(e)}")



class AdvancedControlPanel(QGroupBox):
    """고급 제어 패널"""

    def __init__(self, connection_panel):
        super().__init__("고급 제어")
        self.connection_panel = connection_panel
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # 타이밍 설정
        timing_group = QGroupBox("타이밍 설정")
        timing_layout = QGridLayout()

        timing_layout.addWidget(QLabel("Coincidence Window:"), 0, 0)
        self.coincidence_spin = QSpinBox()
        self.coincidence_spin.setRange(0, 255)
        self.coincidence_spin.setValue(128)
        timing_layout.addWidget(self.coincidence_spin, 0, 1)

        self.coincidence_btn = QPushButton("설정")
        self.coincidence_btn.clicked.connect(self.set_coincidence_window)
        timing_layout.addWidget(self.coincidence_btn, 0, 2)

        timing_layout.addWidget(QLabel("Shaper Offset:"), 1, 0)
        self.shaper_offset_spin = QSpinBox()
        self.shaper_offset_spin.setRange(0, 200)
        self.shaper_offset_spin.setValue(100)
        timing_layout.addWidget(self.shaper_offset_spin, 1, 1)

        self.shaper_offset_btn = QPushButton("설정")
        self.shaper_offset_btn.clicked.connect(self.set_shaper_offset)
        timing_layout.addWidget(self.shaper_offset_btn, 1, 2)

        timing_layout.addWidget(QLabel("Threshold Offset:"), 2, 0)
        self.threshold_offset_spin = QSpinBox()
        self.threshold_offset_spin.setRange(0, 200)
        self.threshold_offset_spin.setValue(100)
        timing_layout.addWidget(self.threshold_offset_spin, 2, 1)

        self.threshold_offset_btn = QPushButton("설정")
        self.threshold_offset_btn.clicked.connect(self.set_threshold_offset)
        timing_layout.addWidget(self.threshold_offset_btn, 2, 2)

        timing_group.setLayout(timing_layout)
        layout.addWidget(timing_group)

        # 모드 설정
        mode_group = QGroupBox("모드 설정")
        mode_layout = QVBoxLayout()

        self.single_channel_check = QCheckBox("Single Channel Mode")
        mode_layout.addWidget(self.single_channel_check)

        self.ecl_delay_check = QCheckBox("ECL Delay")
        mode_layout.addWidget(self.ecl_delay_check)

        self.blr_mode_check = QCheckBox("BLR Mode")
        self.blr_mode_check.setChecked(True)
        mode_layout.addWidget(self.blr_mode_check)

        self.mode_btn = QPushButton("모드 설정 적용")
        self.mode_btn.clicked.connect(self.apply_mode_settings)
        mode_layout.addWidget(self.mode_btn)

        mode_group.setLayout(mode_layout)
        layout.addWidget(mode_group)

        # Multiplicity 설정
        multiplicity_group = QGroupBox("Multiplicity 설정")
        multiplicity_layout = QGridLayout()

        multiplicity_layout.addWidget(QLabel("High:"), 0, 0)
        self.multiplicity_hi_spin = QSpinBox()
        self.multiplicity_hi_spin.setRange(1, 9)
        self.multiplicity_hi_spin.setValue(5)
        multiplicity_layout.addWidget(self.multiplicity_hi_spin, 0, 1)

        multiplicity_layout.addWidget(QLabel("Low:"), 1, 0)
        self.multiplicity_lo_spin = QSpinBox()
        self.multiplicity_lo_spin.setRange(1, 8)
        self.multiplicity_lo_spin.setValue(2)
        multiplicity_layout.addWidget(self.multiplicity_lo_spin, 1, 1)

        self.multiplicity_btn = QPushButton("설정")
        self.multiplicity_btn.clicked.connect(self.set_multiplicity_borders)
        multiplicity_layout.addWidget(self.multiplicity_btn, 2, 0, 1, 2)

        multiplicity_group.setLayout(multiplicity_layout)
        layout.addWidget(multiplicity_group)

        # RC 모드 제어
        rc_group = QGroupBox("RC 모드")
        rc_layout = QHBoxLayout()

        self.rc_on_btn = QPushButton("RC 모드 ON")
        self.rc_on_btn.clicked.connect(self.switch_rc_mode_on)
        rc_layout.addWidget(self.rc_on_btn)

        self.rc_off_btn = QPushButton("RC 모드 OFF")
        self.rc_off_btn.clicked.connect(self.switch_rc_mode_off)
        rc_layout.addWidget(self.rc_off_btn)

        rc_group.setLayout(rc_layout)
        layout.addWidget(rc_group)

        self.setLayout(layout)

    def set_coincidence_window(self):
        """Coincidence Window 설정"""
        if not self.connection_panel.is_connected:
            QMessageBox.warning(self, "경고", "장치에 연결되지 않았습니다.")
            return

        try:
            value = self.coincidence_spin.value()
            self.connection_panel.controller.set_coincidence_window(value)
            QMessageBox.information(self, "성공", f"Coincidence Window가 {value}로 설정되었습니다.")

        except MSCF16Error as e:
            QMessageBox.critical(self, "오류", f"Coincidence Window 설정 실패:\n{str(e)}")

    def set_shaper_offset(self):
        """Shaper Offset 설정"""
        if not self.connection_panel.is_connected:
            QMessageBox.warning(self, "경고", "장치에 연결되지 않았습니다.")
            return

        try:
            value = self.shaper_offset_spin.value()
            self.connection_panel.controller.set_shaper_offset(value)
            QMessageBox.information(self, "성공", f"Shaper Offset이 {value}로 설정되었습니다.")

        except MSCF16Error as e:
            QMessageBox.critical(self, "오류", f"Shaper Offset 설정 실패:\n{str(e)}")

    def set_threshold_offset(self):
        """Threshold Offset 설정"""
        if not self.connection_panel.is_connected:
            QMessageBox.warning(self, "경고", "장치에 연결되지 않았습니다.")
            return

        try:
            value = self.threshold_offset_spin.value()
            self.connection_panel.controller.set_threshold_offset(value)
            QMessageBox.information(self, "성공", f"Threshold Offset이 {value}로 설정되었습니다.")

        except MSCF16Error as e:
            QMessageBox.critical(self, "오류", f"Threshold Offset 설정 실패:\n{str(e)}")

    def apply_mode_settings(self):
        """모드 설정 적용"""
        if not self.connection_panel.is_connected:
            QMessageBox.warning(self, "경고", "장치에 연결되지 않았습니다.")
            return

        try:
            self.connection_panel.controller.set_single_channel_mode(self.single_channel_check.isChecked())
            self.connection_panel.controller.set_ecl_delay(self.ecl_delay_check.isChecked())
            self.connection_panel.controller.set_blr_mode(self.blr_mode_check.isChecked())

            QMessageBox.information(self, "성공", "모드 설정이 적용되었습니다.")

        except MSCF16Error as e:
            QMessageBox.critical(self, "오류", f"모드 설정 실패:\n{str(e)}")

    def set_multiplicity_borders(self):
        """Multiplicity Borders 설정"""
        if not self.connection_panel.is_connected:
            QMessageBox.warning(self, "경고", "장치에 연결되지 않았습니다.")
            return

        try:
            hi = self.multiplicity_hi_spin.value()
            lo = self.multiplicity_lo_spin.value()

            self.connection_panel.controller.set_multiplicity_borders(hi, lo)
            QMessageBox.information(self, "성공", f"Multiplicity Borders가 High: {hi}, Low: {lo}로 설정되었습니다.")

        except MSCF16Error as e:
            QMessageBox.critical(self, "오류", f"Multiplicity Borders 설정 실패:\n{str(e)}")

    def switch_rc_mode_on(self):
        """RC 모드 ON"""
        if not self.connection_panel.is_connected:
            QMessageBox.warning(self, "경고", "장치에 연결되지 않았습니다.")
            return

        try:
            self.connection_panel.controller.switch_rc_mode_on()
            QMessageBox.information(self, "성공", "RC 모드가 활성화되었습니다.")

        except MSCF16Error as e:
            QMessageBox.critical(self, "오류", f"RC 모드 활성화 실패:\n{str(e)}")

    def switch_rc_mode_off(self):
        """RC 모드 OFF"""
        if not self.connection_panel.is_connected:
            QMessageBox.warning(self, "경고", "장치에 연결되지 않았습니다.")
            return

        try:
            self.connection_panel.controller.switch_rc_mode_off()
            QMessageBox.information(self, "성공", "RC 모드가 비활성화되었습니다.")

        except MSCF16Error as e:
            QMessageBox.critical(self, "오류", f"RC 모드 비활성화 실패:\n{str(e)}")


class StatusPanel(QGroupBox):
    """상태 표시 및 로그 패널"""

    def __init__(self, connection_panel):
        super().__init__("상태 및 로그")
        self.connection_panel = connection_panel
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # 장치 정보
        info_group = QGroupBox("장치 정보")
        info_layout = QGridLayout()

        self.version_label = QLabel("버전: 알 수 없음")
        info_layout.addWidget(self.version_label, 0, 0)

        self.version_btn = QPushButton("버전 확인")
        self.version_btn.clicked.connect(self.get_version)
        info_layout.addWidget(self.version_btn, 0, 1)

        self.setup_btn = QPushButton("설정 표시")
        self.setup_btn.clicked.connect(self.display_setup)
        info_layout.addWidget(self.setup_btn, 0, 2)

        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        # 로그 영역
        log_group = QGroupBox("로그")
        log_layout = QVBoxLayout()

        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(200)
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)

        clear_btn = QPushButton("로그 지우기")
        clear_btn.clicked.connect(self.clear_log)
        log_layout.addWidget(clear_btn)

        log_group.setLayout(log_layout)
        layout.addWidget(log_group)

        self.setLayout(layout)

    def log_message(self, message):
        """로그 메시지 추가"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")

    def clear_log(self):
        """로그 지우기"""
        self.log_text.clear()

    def get_version(self):
        """펌웨어 버전 확인"""
        if not self.connection_panel.is_connected:
            QMessageBox.warning(self, "경고", "장치에 연결되지 않았습니다.")
            return

        try:
            version = self.connection_panel.controller.get_version()
            self.version_label.setText(f"버전: {version}")
            self.log_message(f"펌웨어 버전: {version}")

        except MSCF16Error as e:
            QMessageBox.critical(self, "오류", f"버전 확인 실패:\n{str(e)}")

    def display_setup(self):
        """설정 표시"""
        if not self.connection_panel.is_connected:
            QMessageBox.warning(self, "경고", "장치에 연결되지 않았습니다.")
            return

        try:
            setup_info = self.connection_panel.controller.display_setup()
            self.log_message("현재 설정:")
            self.log_message(setup_info)

            # 별도 창으로 표시
            msg_box = QMessageBox()
            msg_box.setWindowTitle("현재 설정")
            msg_box.setText(setup_info)
            msg_box.setDetailedText(setup_info)
            msg_box.exec_()

        except MSCF16Error as e:
            QMessageBox.critical(self, "오류", f"설정 표시 실패:\n{str(e)}")


class MSCF16MainWindow(QMainWindow):
    """MSCF-16 메인 윈도우"""

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("MSCF-16 NIM Device Controller")
        self.setGeometry(100, 100, 1200, 800)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout()

        # Connection panel
        self.connection_panel = ConnectionPanel()
        self.connection_panel.connection_changed.connect(self.on_connection_changed)
        main_layout.addWidget(self.connection_panel)

        # Tab widget
        tab_widget = QTabWidget()

        # Combined control tab
        combined_tab = CombinedControlPanel(self.connection_panel)
        tab_widget.addTab(combined_tab, "Channel & Group Control")

        # Advanced control tab
        advanced_tab = QWidget()
        advanced_layout = QVBoxLayout()
        self.advanced_panel = AdvancedControlPanel(self.connection_panel)
        advanced_layout.addWidget(self.advanced_panel)
        advanced_tab.setLayout(advanced_layout)
        tab_widget.addTab(advanced_tab, "Advanced Control")

        # Status tab
        status_tab = QWidget()
        status_layout = QVBoxLayout()
        self.status_panel = StatusPanel(self.connection_panel)
        status_layout.addWidget(self.status_panel)
        status_tab.setLayout(status_layout)
        tab_widget.addTab(status_tab, "Status & Log")

        main_layout.addWidget(tab_widget)
        central_widget.setLayout(main_layout)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

        # Set initial UI state based on connection status
        self.on_connection_changed(False)

    def on_connection_changed(self, connected):
        """Called when connection status changes"""
        if connected:
            self.status_bar.showMessage("Device Connected")
            self.status_panel.log_message("Device connected.")
        else:
            self.status_bar.showMessage("Device Not Connected")
            self.status_panel.log_message("Device disconnected.")

    def closeEvent(self, event):
        """Called when window is closed"""
        if self.connection_panel.is_connected:
            reply = QMessageBox.question(self, 'Exit Confirmation',
                                       'Device is connected. Are you sure you want to exit?',
                                       QMessageBox.Yes | QMessageBox.No,
                                       QMessageBox.No)

            if reply == QMessageBox.Yes:
                self.connection_panel.disconnect_device()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


def main():
    """Main function"""
    app = QApplication(sys.argv)

    # Set application information
    app.setApplicationName("MSCF-16 Controller")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("MSCF-16")

    # Create and show main window
    window = MSCF16MainWindow()
    window.show()

    # Start event loop
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
