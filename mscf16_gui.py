"""
MSCF-16 NIM Device GUI Application

PyQt5-based GUI application for controlling MSCF-16 device
"""

from re import A
import sys
import serial.tools.list_ports
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                            QHBoxLayout, QTabWidget, QLabel, QPushButton,
                            QComboBox, QSpinBox, QCheckBox, QGroupBox,
                            QTextEdit, QStatusBar, QMessageBox, QGridLayout,
                            QSlider, QProgressBar, QSplitter, QDialog, QScrollArea)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QIcon
from mscf16_controller import MSCF16Controller, MSCF16Error
from mscf16_constants import Parameters


class ConnectionPanel(QGroupBox):
    """Connection Settings Panel"""

    connection_changed = pyqtSignal(bool)  # Connection status change signal
    connection_success = pyqtSignal(object, str, int)  # Emits (controller, port, baudrate) on successful connection

    def __init__(self):
        super().__init__("Connection Settings")
        self.controller = None
        self.is_connected = False
        self.init_ui()
        self.refresh_ports()


    def init_ui(self):
        self.setContentsMargins(1, 1, 1, 1)

        layout = QVBoxLayout()
        layout.setSpacing(1)

        # First row: Connection settings
        connection_layout = QHBoxLayout()
        connection_layout.setSpacing(2)

        # Port selection
        connection_layout.addWidget(QLabel("Port:"))
        self.port_combo = QComboBox()
        self.port_combo.setMinimumWidth(200)
        connection_layout.addWidget(self.port_combo)

        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.refresh_ports)
        connection_layout.addWidget(self.refresh_btn)

        # Baud rate selection
        connection_layout.addWidget(QLabel("Baud Rate:"))
        self.baudrate_combo = QComboBox()
        self.baudrate_combo.addItems(["9600", "19200", "28400", "57600", "115200"])
        self.baudrate_combo.setCurrentText("9600")
        connection_layout.addWidget(self.baudrate_combo)

        # Connection button
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self.toggle_connection)
        connection_layout.addWidget(self.connect_btn)
        connection_layout.addStretch()

        layout.addLayout(connection_layout)

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
                return None, None, None

            port = port_text.split(" - ")[0]
            baudrate = int(self.baudrate_combo.currentText())

            controller = MSCF16Controller(port=port, baudrate=baudrate)
            controller.connect()

            # Emit signal to create tab (controller is passed to tab, not stored here)
            self.connection_success.emit(controller, port, baudrate)

            # Reset connection state after emitting signal so UI is ready for next connection
            QTimer.singleShot(100, self.reset_connection_state)

            QMessageBox.information(self, "Success", f"Connected to device.\nPort: {port}\nBaud Rate: {baudrate}")
            return controller, port, baudrate

        except MSCF16Error as e:
            QMessageBox.critical(self, "Connection Error", f"Failed to connect to device:\n{str(e)}")
            return None, None, None
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Unexpected error occurred:\n{str(e)}")
            return None, None, None

    def disconnect_device(self):
        """Disconnect from device"""
        try:
            if self.controller:
                self.controller.disconnect()
                self.controller = None

            self.is_connected = False
            self.update_ui()
            self.connection_changed.emit(False)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error occurred during disconnection:\n{str(e)}")

    def reset_connection_state(self):
        """Reset connection state after device is connected"""
        self.is_connected = False
        self.controller = None
        self.update_ui()

    def update_ui(self):
        """Update UI state"""
        if self.is_connected:
            self.connect_btn.setText("Disconnect")
            self.port_combo.setEnabled(False)
            self.baudrate_combo.setEnabled(False)
            self.refresh_btn.setEnabled(False)
        else:
            self.connect_btn.setText("Connect")
            self.port_combo.setEnabled(True)
            self.baudrate_combo.setEnabled(True)
            self.refresh_btn.setEnabled(True)


class ControlPanel(QWidget):
    """Channel and Group Control Panel"""

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
        threshold_group.setContentsMargins(1, 4, 1, 1)
        threshold_layout = QVBoxLayout()
        threshold_layout.setSpacing(0)

        # Individual channel Threshold settings
        individual_threshold_layout = QGridLayout()
        individual_threshold_layout.setSpacing(2)
        # Channel Threshold value input (2 rows)
        self.threshold_spins = {}
        for row in range(2):
            for col in range(8):
                channel_num = row * 8 + col + 1

                # Channel number label
                channel_label = QLabel(f"CH{channel_num:02d}")
                channel_label.setFixedWidth(35)
                individual_threshold_layout.addWidget(channel_label, row, 3*col, alignment=Qt.AlignVCenter)

                # Threshold value input
                spin_box = QSpinBox()
                spin_box.setRange(0, 255)
                spin_box.setValue(128)
                spin_box.setFixedWidth(50)
                self.threshold_spins[channel_num] = spin_box
                individual_threshold_layout.addWidget(spin_box, row, 3*col+1)

                # Set button
                btn = QPushButton("Set")
                btn.setFixedSize(50, 24)
                btn.clicked.connect(lambda checked, ch=channel_num: self.set_threshold(ch))
                individual_threshold_layout.addWidget(btn, row, 3*col+2, Qt.AlignTop)

        threshold_layout.addLayout(individual_threshold_layout)

        # Common Threshold settings
        common_threshold_layout = QHBoxLayout()
        common_threshold_layout.setSpacing(2)
        common_threshold_layout.addWidget(QLabel("Common:"))
        self.common_threshold_spin = QSpinBox()
        self.common_threshold_spin.setRange(0, 255)
        self.common_threshold_spin.setValue(128)
        self.common_threshold_spin.setFixedWidth(60)
        common_threshold_layout.addWidget(self.common_threshold_spin, alignment=Qt.AlignVCenter)
        common_threshold_layout.addSpacing(10)
        common_btn = QPushButton("Apply to All Channels")
        common_btn.setFixedSize(150, 24)
        common_btn.setStyleSheet("QPushButton { background-color: #ffcccc; font-weight: bold; }")
        common_btn.clicked.connect(lambda: self.set_threshold(17))
        common_threshold_layout.addWidget(common_btn, alignment=Qt.AlignVCenter)
        common_threshold_layout.addStretch()

        threshold_layout.addLayout(common_threshold_layout)
        threshold_group.setLayout(threshold_layout)
        channel_layout.addWidget(threshold_group)

        # PZ value settings
        pz_group = QGroupBox("PZ Value Settings")
        pz_group.setContentsMargins(1, 4, 1, 1)
        pz_layout = QVBoxLayout()
        pz_layout.setSpacing(0)
        # Individual channel PZ settings
        individual_pz_layout = QGridLayout()
        individual_pz_layout.setSpacing(0)

        # Channel PZ value input (2 rows)
        self.pz_spins = {}
        for row in range(2):
            for col in range(8):
                channel_num = row * 8 + col + 1

                # Channel number label
                channel_label = QLabel(f"CH{channel_num:02d}")
                channel_label.setFixedWidth(35)
                individual_pz_layout.addWidget(channel_label, row, 3*col, alignment=Qt.AlignVCenter)

                # PZ value input
                spin_box = QSpinBox()
                spin_box.setRange(0, 255)
                spin_box.setValue(100)
                spin_box.setFixedWidth(50)
                self.pz_spins[channel_num] = spin_box
                individual_pz_layout.addWidget(spin_box, row, 3*col+1)

                # Set button
                btn = QPushButton("Set")
                btn.setFixedSize(50, 24)
                btn.clicked.connect(lambda checked, ch=channel_num: self.set_pz_value(ch))
                individual_pz_layout.addWidget(btn, row, 3*col+2, Qt.AlignTop)

        pz_layout.addLayout(individual_pz_layout)

        # Common PZ settings
        common_pz_layout = QHBoxLayout()
        common_pz_layout.setSpacing(2)
        common_pz_layout.addWidget(QLabel("Common:"))
        self.common_pz_spin = QSpinBox()
        self.common_pz_spin.setRange(0, 255)
        self.common_pz_spin.setValue(100)
        self.common_pz_spin.setFixedWidth(60)
        common_pz_layout.addWidget(self.common_pz_spin, alignment=Qt.AlignVCenter)
        common_pz_layout.addSpacing(10)
        common_pz_btn = QPushButton("Apply to All Channels")
        common_pz_btn.setFixedSize(150, 24)
        common_pz_btn.setStyleSheet("QPushButton { background-color: #ccffcc; font-weight: bold; }")
        common_pz_btn.clicked.connect(lambda: self.set_pz_value(17))
        common_pz_layout.addWidget(common_pz_btn, alignment=Qt.AlignVCenter)
        common_pz_layout.addStretch()

        pz_layout.addLayout(common_pz_layout)
        pz_group.setLayout(pz_layout)
        channel_layout.addWidget(pz_group)

        # Monitor and Automatic PZ settings side by side
        monitor_auto_pz_layout = QHBoxLayout()
        monitor_auto_pz_layout.setSpacing(2)

        # Monitor channel settings
        monitor_group = QGroupBox("Monitor Channel Settings")
        monitor_group.setContentsMargins(1, 4, 1, 1)

        monitor_layout = QHBoxLayout()
        monitor_layout.setSpacing(2)
        monitor_layout.addWidget(QLabel("Monitor Channel:"))
        self.monitor_combo = QComboBox()
        self.monitor_combo.addItems([f"CH{i:02d}" for i in range(1, 17)])
        self.monitor_combo.setCurrentIndex(0)
        self.monitor_combo.currentIndexChanged.connect(self._on_monitor_channel_changed)
        monitor_layout.addWidget(self.monitor_combo, alignment=Qt.AlignVCenter)
        monitor_layout.addStretch()

        monitor_group.setLayout(monitor_layout)
        monitor_auto_pz_layout.addWidget(monitor_group)

        # Automatic PZ settings
        auto_pz_group = QGroupBox("Automatic PZ Settings")
        auto_pz_group.setContentsMargins(1, 4, 1, 1)

        auto_pz_layout = QHBoxLayout()
        auto_pz_layout.setSpacing(2)
        auto_pz_layout.addWidget(QLabel("Channel:"))
        self.auto_pz_combo = QComboBox()
        self.auto_pz_combo.addItem("All")
        self.auto_pz_combo.addItems([f"CH{i:02d}" for i in range(1, 17)])
        self.auto_pz_combo.setCurrentIndex(0)
        auto_pz_layout.addWidget(self.auto_pz_combo, alignment=Qt.AlignVCenter)

        self.auto_pz_set_btn = QPushButton("Set")
        self.auto_pz_set_btn.setFixedSize(50, 24)
        self.auto_pz_set_btn.clicked.connect(self.set_automatic_pz)
        auto_pz_layout.addWidget(self.auto_pz_set_btn, alignment=Qt.AlignTop)
        auto_pz_layout.addStretch()

        auto_pz_group.setLayout(auto_pz_layout)
        monitor_auto_pz_layout.addWidget(auto_pz_group)

        channel_layout.addLayout(monitor_auto_pz_layout)

        channel_widget.setLayout(channel_layout)
        splitter.addWidget(channel_widget)

        # Bottom side: Group Control
        group_widget = QWidget()
        group_layout = QVBoxLayout()

        # Shaping Time settings
        shaping_group = QGroupBox("Shaping Time Settings")
        shaping_group.setContentsMargins(1, 4, 1, 1)

        # Group Shaping Time value input (2x2 grid)
        self.shaping_spins = {}
        row_layout = QHBoxLayout()
        row_layout.setSpacing(5)

        for group_num in range(1, 5):
            # Group number label
            group_label = QLabel(f"G{group_num}:")
            group_label.setFixedWidth(18)
            row_layout.addWidget(group_label)

            spin_box = QSpinBox()
            spin_box.setRange(0, 15)
            spin_box.setValue(8)
            spin_box.setFixedWidth(40)
            self.shaping_spins[group_num] = spin_box
            row_layout.addWidget(spin_box, alignment=Qt.AlignVCenter)

            # Set button
            btn = QPushButton("Set")
            btn.setFixedSize(50, 24)
            btn.clicked.connect(lambda checked, g=group_num: self.set_shaping_time(g))
            row_layout.addWidget(btn, alignment=Qt.AlignTop)

        # Common Shaping Time settings
        row_layout.addWidget(QLabel("Common:"))
        self.common_shaping_spin = QSpinBox()
        self.common_shaping_spin.setRange(0, 15)
        self.common_shaping_spin.setValue(8)
        self.common_shaping_spin.setFixedWidth(40)
        row_layout.addWidget(self.common_shaping_spin, alignment=Qt.AlignVCenter)
        row_layout.addSpacing(10)
        common_shaping_btn = QPushButton("Apply to All Groups")
        common_shaping_btn.setFixedSize(150, 24)
        common_shaping_btn.setStyleSheet("QPushButton { background-color: #ffddcc; font-weight: bold; }")
        common_shaping_btn.clicked.connect(lambda: self.set_shaping_time(5))
        row_layout.addWidget(common_shaping_btn, alignment=Qt.AlignVCenter)

        row_layout.addStretch()
        shaping_group.setLayout(row_layout)
        group_layout.addWidget(shaping_group)

        # Gain settings
        gain_group = QGroupBox("Gain Settings")
        gain_group.setContentsMargins(1, 4, 1, 1)
        gain_layout = QHBoxLayout()
        gain_layout.setSpacing(5)

        # Individual group Gain settings
        # Group Gain value input (2x2 grid)
        self.gain_spins = {}
        for group_num in range(1, 5):
            # Group number label
            group_label = QLabel(f"G{group_num}:")
            group_label.setFixedWidth(18)
            gain_layout.addWidget(group_label)

            # Gain value input
            spin_box = QSpinBox()
            spin_box.setRange(0, 15)
            spin_box.setValue(8)
            spin_box.setFixedWidth(40)
            self.gain_spins[group_num] = spin_box
            gain_layout.addWidget(spin_box, alignment=Qt.AlignVCenter)

            # Set button
            btn = QPushButton("Set")
            btn.setFixedSize(50, 24)
            btn.clicked.connect(lambda checked, g=group_num: self.set_gain(g))
            gain_layout.addWidget(btn, alignment=Qt.AlignTop)

        # Common Gain settings
        gain_layout.addWidget(QLabel("Common:"))
        self.common_gain_spin = QSpinBox()
        self.common_gain_spin.setRange(0, 15)
        self.common_gain_spin.setValue(8)
        self.common_gain_spin.setFixedWidth(40)
        gain_layout.addWidget(self.common_gain_spin, alignment=Qt.AlignVCenter)
        gain_layout.addSpacing(10)
        common_gain_btn = QPushButton("Apply to All Groups")
        common_gain_btn.setFixedSize(150, 24)
        common_gain_btn.setStyleSheet("QPushButton { background-color: #ddffdd; font-weight: bold; }")
        common_gain_btn.clicked.connect(lambda: self.set_gain(5))
        gain_layout.addWidget(common_gain_btn, alignment=Qt.AlignVCenter)
        gain_layout.addStretch()

        gain_group.setLayout(gain_layout)
        group_layout.addWidget(gain_group)

        group_widget.setLayout(group_layout)
        splitter.addWidget(group_widget)

        # Set splitter proportions (60% channel, 40% group)
        splitter.setSizes([350, 250])

        layout.addWidget(splitter)

        # General Settings (combining Timing and Multiplicity)
        general_group = QGroupBox("General Settings")
        general_group.setContentsMargins(1, 4, 1, 1)
        general_layout = QGridLayout()
        general_layout.setSpacing(2)

        # Timing settings in one line
        timing_layout = QHBoxLayout()
        timing_layout.setSpacing(2)

        general_layout.addWidget(QLabel("Coincidence Window:"), 0, 0)
        self.coincidence_spin = QSpinBox()
        self.coincidence_spin.setRange(0, 255)
        self.coincidence_spin.setValue(128)
        self.coincidence_spin.setFixedWidth(60)
        general_layout.addWidget(self.coincidence_spin, 0, 1)

        self.coincidence_btn = QPushButton("Set")
        self.coincidence_btn.setFixedSize(50, 24)
        self.coincidence_btn.clicked.connect(self.set_coincidence_window)
        general_layout.addWidget(self.coincidence_btn, 0, 2, alignment=Qt.AlignTop)

        general_layout.addWidget(QLabel("Shaper Offset:"), 0, 3)
        self.shaper_offset_spin = QSpinBox()
        self.shaper_offset_spin.setRange(0, 200)
        self.shaper_offset_spin.setValue(100)
        self.shaper_offset_spin.setFixedWidth(60)
        general_layout.addWidget(self.shaper_offset_spin, 0, 4)

        self.shaper_offset_btn = QPushButton("Set")
        self.shaper_offset_btn.setFixedSize(50, 24)
        self.shaper_offset_btn.clicked.connect(self.set_shaper_offset)
        general_layout.addWidget(self.shaper_offset_btn, 0, 5, alignment=Qt.AlignTop)

        general_layout.addWidget(QLabel("Threshold Offset:"), 0, 6)
        self.threshold_offset_spin = QSpinBox()
        self.threshold_offset_spin.setRange(0, 200)
        self.threshold_offset_spin.setValue(100)
        self.threshold_offset_spin.setFixedWidth(60)
        general_layout.addWidget(self.threshold_offset_spin, 0, 7)

        self.threshold_offset_btn = QPushButton("Set")
        self.threshold_offset_btn.setFixedSize(50, 24)
        self.threshold_offset_btn.clicked.connect(self.set_threshold_offset)
        general_layout.addWidget(self.threshold_offset_btn, 0, 8, alignment=Qt.AlignTop)

        general_layout.addWidget(QLabel("BLR Threshold:"), 0, 9)
        self.blr_threshold_spin = QSpinBox()
        self.blr_threshold_spin.setRange(0, 255)
        self.blr_threshold_spin.setValue(128)
        self.blr_threshold_spin.setFixedWidth(60)
        general_layout.addWidget(self.blr_threshold_spin, 0, 10)

        self.blr_threshold_btn = QPushButton("Set")
        self.blr_threshold_btn.setFixedSize(50, 24)
        self.blr_threshold_btn.clicked.connect(self.set_blr_threshold)
        general_layout.addWidget(self.blr_threshold_btn, 0, 11, alignment=Qt.AlignTop)
        general_layout.setColumnStretch(12, 1)

        # Multiplicity settings in one line
        general_layout.addWidget(QLabel("Multiplicity High:"), 1, 0)
        self.multiplicity_hi_spin = QSpinBox()
        self.multiplicity_hi_spin.setRange(1, 9)
        self.multiplicity_hi_spin.setValue(5)
        self.multiplicity_hi_spin.setFixedWidth(60)
        general_layout.addWidget(self.multiplicity_hi_spin, 1, 1)

        general_layout.addWidget(QLabel("Low:"), 1, 3)
        self.multiplicity_lo_spin = QSpinBox()
        self.multiplicity_lo_spin.setRange(1, 8)
        self.multiplicity_lo_spin.setValue(2)
        self.multiplicity_lo_spin.setFixedWidth(60)
        general_layout.addWidget(self.multiplicity_lo_spin, 1, 4)

        self.multiplicity_btn = QPushButton("Set")
        self.multiplicity_btn.setFixedSize(50, 24)
        self.multiplicity_btn.clicked.connect(self.set_multiplicity_borders)
        general_layout.addWidget(self.multiplicity_btn, 1, 5, alignment=Qt.AlignTop)

        general_layout.addWidget(QLabel("Timing Filter Int. Time:"), 1, 6)
        self.timing_filter_combo = QComboBox()
        self.timing_filter_combo.addItems(["0", "1", "2", "3"])
        self.timing_filter_combo.setCurrentIndex(0)
        self.timing_filter_combo.currentIndexChanged.connect(self.set_timing_filter)
        general_layout.addWidget(self.timing_filter_combo, 1, 7, alignment=Qt.AlignVCenter)

        general_group.setLayout(general_layout)
        layout.addWidget(general_group)

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

    def _on_monitor_channel_changed(self, index):
        """Handle monitor channel dropdown change"""
        if not self.connection_panel.is_connected:
            # Revert selection if not connected
            self.monitor_combo.blockSignals(True)
            self.monitor_combo.setCurrentIndex(0)
            self.monitor_combo.blockSignals(False)
            return

        try:
            channel = index + 1  # ComboBox index is 0-based, channel is 1-based
            self.connection_panel.controller.set_monitor_channel(channel)
            QMessageBox.information(self, "Success", f"Channel {channel} set as monitor channel.")
        except MSCF16Error as e:
            QMessageBox.critical(self, "Error", f"Monitor channel setting failed:\n{str(e)}")
            # Revert selection on error
            self.monitor_combo.blockSignals(True)
            self.monitor_combo.setCurrentIndex(0)
            self.monitor_combo.blockSignals(False)

    def set_automatic_pz(self):
        """Set Automatic PZ for selected channel or all channels"""
        if not self.connection_panel.is_connected:
            QMessageBox.warning(self, "Warning", "Device is not connected.")
            return

        try:
            selected_index = self.auto_pz_combo.currentIndex()
            if selected_index == 0:
                # "All" selected - set automatic PZ for all channels
                self.connection_panel.controller.toggle_automatic_pz()
                QMessageBox.information(self, "Success", "Automatic PZ set for all channels.")
            else:
                # Specific channel selected (index 1-16 corresponds to CH1-CH16)
                channel = selected_index  # index 1 = CH1, index 2 = CH2, etc.
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

    def set_coincidence_window(self):
        """Set Coincidence Window"""
        if not self.connection_panel.is_connected:
            QMessageBox.warning(self, "Warning", "Device is not connected.")
            return

        try:
            value = self.coincidence_spin.value()
            self.connection_panel.controller.set_coincidence_window(value)
            QMessageBox.information(self, "Success", f"Coincidence Window set to {value}.")

        except MSCF16Error as e:
            QMessageBox.critical(self, "Error", f"Coincidence Window setting failed:\n{str(e)}")

    def set_shaper_offset(self):
        """Set Shaper Offset"""
        if not self.connection_panel.is_connected:
            QMessageBox.warning(self, "Warning", "Device is not connected.")
            return

        try:
            value = self.shaper_offset_spin.value()
            self.connection_panel.controller.set_shaper_offset(value)
            QMessageBox.information(self, "Success", f"Shaper Offset set to {value}.")

        except MSCF16Error as e:
            QMessageBox.critical(self, "Error", f"Shaper Offset setting failed:\n{str(e)}")

    def set_threshold_offset(self):
        """Set Threshold Offset"""
        if not self.connection_panel.is_connected:
            QMessageBox.warning(self, "Warning", "Device is not connected.")
            return

        try:
            value = self.threshold_offset_spin.value()
            self.connection_panel.controller.set_threshold_offset(value)
            QMessageBox.information(self, "Success", f"Threshold Offset set to {value}.")

        except MSCF16Error as e:
            QMessageBox.critical(self, "Error", f"Threshold Offset setting failed:\n{str(e)}")

    def set_blr_threshold(self):
        """Set BLR Threshold"""
        if not self.connection_panel.is_connected:
            QMessageBox.warning(self, "Warning", "Device is not connected.")
            return

        try:
            value = self.blr_threshold_spin.value()
            self.connection_panel.controller.set_blr_threshold(value)
            QMessageBox.information(self, "Success", f"BLR Threshold set to {value}.")

        except MSCF16Error as e:
            QMessageBox.critical(self, "Error", f"BLR Threshold setting failed:\n{str(e)}")

    def set_multiplicity_borders(self):
        """Set Multiplicity Borders"""
        if not self.connection_panel.is_connected:
            QMessageBox.warning(self, "Warning", "Device is not connected.")
            return

        try:
            hi = self.multiplicity_hi_spin.value()
            lo = self.multiplicity_lo_spin.value()

            self.connection_panel.controller.set_multiplicity_borders(hi, lo)
            QMessageBox.information(self, "Success", f"Multiplicity Borders set to High: {hi}, Low: {lo}.")

        except MSCF16Error as e:
            QMessageBox.critical(self, "Error", f"Multiplicity Borders setting failed:\n{str(e)}")

    def set_timing_filter(self, index):
        """Set Timing Filter Integration Time (called when combo box changes)"""
        if not self.connection_panel.is_connected:
            # Revert selection if not connected
            self.timing_filter_combo.blockSignals(True)
            self.timing_filter_combo.setCurrentIndex(0)
            self.timing_filter_combo.blockSignals(False)
            return

        try:
            value = index  # ComboBox index matches the value (0-3)
            self.connection_panel.controller.set_timing_filter(value)
            # Success message is optional - you can remove this if too verbose
            # QMessageBox.information(self, "Success", f"Timing Filter Integration Time set to {value}.")

        except MSCF16Error as e:
            QMessageBox.critical(self, "Error", f"Timing Filter setting failed:\n{str(e)}")
            # Revert selection on error
            self.timing_filter_combo.blockSignals(True)
            self.timing_filter_combo.setCurrentIndex(0)
            self.timing_filter_combo.blockSignals(False)


class DeviceTab(QWidget):
    """Individual device tab widget"""

    def __init__(self, parent_window, controller, port, baudrate):
        super().__init__()
        self.parent_window = parent_window
        self.controller = controller
        self.port = port
        self.baudrate = baudrate
        self.is_connected = True
        self.init_ui()
        self.on_connection_changed(True)

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(1)
        layout.setContentsMargins(2, 2, 2, 2)

        # Version info and Mode settings
        info_mode_layout = QHBoxLayout()
        # Add spacing only at the beginning of layout
        info_mode_layout.addSpacing(35)

        info_mode_layout.setSpacing(15)  # Reduce spacing between widgets (changed from spacing=50 to 15)
        # Version info
        self.version_label = QLabel("Version: Not connected")
        self.version_label.setStyleSheet("font-weight: bold;")
        info_mode_layout.addWidget(self.version_label, alignment=Qt.AlignBottom)

        # Disconnect button right after version info
        self.disconnect_btn = QPushButton("Disconnect")
        self.disconnect_btn.setFixedSize(110, 24)
        self.disconnect_btn.clicked.connect(self.disconnect_device)
        info_mode_layout.addWidget(self.disconnect_btn, alignment=Qt.AlignTop)

        info_mode_layout.addStretch()

        # View Setting button
        self.view_setting_btn = QPushButton("View Setting")
        self.view_setting_btn.setFixedSize(120, 24)
        self.view_setting_btn.clicked.connect(self.view_settings)
        info_mode_layout.addWidget(self.view_setting_btn, alignment=Qt.AlignTop)

        # Load Setting button
        self.load_setting_btn = QPushButton("Load RC Setting")
        self.load_setting_btn.setFixedSize(120, 24)
        self.load_setting_btn.clicked.connect(self.load_rc_settings)
        info_mode_layout.addWidget(self.load_setting_btn, alignment=Qt.AlignTop)

        # Copy buttons
        self.copy_rc_to_panel_btn = QPushButton("RC→Panel")
        self.copy_rc_to_panel_btn.setFixedSize(100, 24)
        self.copy_rc_to_panel_btn.clicked.connect(self.copy_rc_to_panel)
        info_mode_layout.addWidget(self.copy_rc_to_panel_btn, alignment=Qt.AlignTop)

        self.copy_panel_to_rc_btn = QPushButton("Panel→RC")
        self.copy_panel_to_rc_btn.setFixedSize(100, 24)
        self.copy_panel_to_rc_btn.clicked.connect(self.copy_panel_to_rc)
        info_mode_layout.addWidget(self.copy_panel_to_rc_btn, alignment=Qt.AlignTop)

        # Mode settings checkboxes
        self.single_channel_check = QCheckBox("Single Mode")
        self.single_channel_check.stateChanged.connect(self._on_single_mode_changed)
        info_mode_layout.addWidget(self.single_channel_check, alignment=Qt.AlignBottom)

        self.ecl_delay_check = QCheckBox("ECL Delay")
        self.ecl_delay_check.stateChanged.connect(self._on_ecl_delay_changed)
        info_mode_layout.addWidget(self.ecl_delay_check, alignment=Qt.AlignBottom)

        self.blr_mode_check = QCheckBox("BLR Mode")
        self.blr_mode_check.setChecked(True)
        self.blr_mode_check.stateChanged.connect(self._on_blr_mode_changed)
        info_mode_layout.addWidget(self.blr_mode_check, alignment=Qt.AlignBottom)

        self.rc_mode_check = QCheckBox("RC Mode")
        self.rc_mode_check.stateChanged.connect(self._on_rc_mode_changed)
        info_mode_layout.addWidget(self.rc_mode_check, alignment=Qt.AlignBottom)
        info_mode_layout.addSpacing(35)

        layout.addLayout(info_mode_layout)

        # Control panel - needs a connection_panel-like object for interface compatibility
        # Create a minimal connection panel wrapper
        class ConnectionWrapper:
            def __init__(self, controller, is_connected):
                self.controller = controller
                self.is_connected = is_connected

        self.connection_wrapper = ConnectionWrapper(self.controller, self.is_connected)
        self.control_panel = ControlPanel(self.connection_wrapper)
        self.control_panel.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.control_panel)

        self.setLayout(layout)

    def disconnect_device(self):
        """Disconnect from device"""
        try:
            if self.controller:
                self.controller.disconnect()
                self.controller = None

            self.is_connected = False
            # Update connection wrapper
            if hasattr(self, 'connection_wrapper'):
                self.connection_wrapper.is_connected = False
                self.connection_wrapper.controller = None
            self.on_connection_changed(False)
            self.parent_window.close_tab_by_widget(self)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error occurred during disconnection:\n{str(e)}")

    def on_connection_changed(self, connected):
        """Called when connection status changes"""
        if connected:
            self.update_version_info()
            self.single_channel_check.setEnabled(True)
            self.ecl_delay_check.setEnabled(True)
            self.blr_mode_check.setEnabled(True)
            self.rc_mode_check.setEnabled(True)
            self.copy_rc_to_panel_btn.setEnabled(True)
            self.copy_panel_to_rc_btn.setEnabled(True)
            self.load_setting_btn.setEnabled(True)
            self.view_setting_btn.setEnabled(True)
            # Update tab title
            if self.controller:
                port = self.port if self.port else 'Connected'
                self.parent_window.update_tab_title(self, port)
        else:
            self.version_label.setText("Version: Not connected")
            self.single_channel_check.setEnabled(False)
            self.ecl_delay_check.setEnabled(False)
            self.blr_mode_check.setEnabled(False)
            self.rc_mode_check.setEnabled(False)
            self.copy_rc_to_panel_btn.setEnabled(False)
            self.copy_panel_to_rc_btn.setEnabled(False)
            self.load_setting_btn.setEnabled(False)
            self.view_setting_btn.setEnabled(False)

    def update_version_info(self):
        """Update version information"""
        if not self.is_connected or not self.controller:
            return

        try:
            sw_version, hw_version = self.controller.get_version_parsed()
            self.version_label.setText(f"SW: {sw_version} | FW: {hw_version}")
        except Exception as e:
            self.version_label.setText(f"Version: Error - {str(e)}")

    def _on_single_mode_changed(self, state):
        """Handle single channel mode checkbox change"""
        if not self.is_connected or not self.controller:
            return

        try:
            enabled = (state == Qt.Checked)
            self.controller.set_single_channel_mode(enabled)
        except MSCF16Error as e:
            QMessageBox.critical(self, "Error", f"Failed to set single mode:\n{str(e)}")
            self.single_channel_check.blockSignals(True)
            self.single_channel_check.setChecked(not enabled)
            self.single_channel_check.blockSignals(False)

    def _on_ecl_delay_changed(self, state):
        """Handle ECL delay checkbox change"""
        if not self.is_connected or not self.controller:
            return

        try:
            enabled = (state == Qt.Checked)
            self.controller.set_ecl_delay(enabled)
        except MSCF16Error as e:
            QMessageBox.critical(self, "Error", f"Failed to set ECL delay:\n{str(e)}")
            self.ecl_delay_check.blockSignals(True)
            self.ecl_delay_check.setChecked(not enabled)
            self.ecl_delay_check.blockSignals(False)

    def _on_blr_mode_changed(self, state):
        """Handle BLR mode checkbox change"""
        if not self.is_connected or not self.controller:
            return

        try:
            enabled = (state == Qt.Checked)
            self.controller.set_blr_mode(enabled)
        except MSCF16Error as e:
            QMessageBox.critical(self, "Error", f"Failed to set BLR mode:\n{str(e)}")
            self.blr_mode_check.blockSignals(True)
            self.blr_mode_check.setChecked(not enabled)
            self.blr_mode_check.blockSignals(False)

    def _on_rc_mode_changed(self, state):
        """Handle RC mode checkbox change"""
        if not self.is_connected or not self.controller:
            return

        try:
            enabled = (state == Qt.Checked)
            if enabled:
                self.controller.switch_rc_mode_on()
            else:
                self.controller.switch_rc_mode_off()
        except MSCF16Error as e:
            QMessageBox.critical(self, "Error", f"Failed to set RC mode:\n{str(e)}")
            self.rc_mode_check.blockSignals(True)
            self.rc_mode_check.setChecked(not enabled)
            self.rc_mode_check.blockSignals(False)

    def copy_rc_to_panel(self):
        """Copy RC settings to front panel"""
        if not self.is_connected:
            QMessageBox.warning(self, "Warning", "Device is not connected.")
            return

        try:
            self.controller.copy_rc_to_front_panel()
            QMessageBox.information(self, "Success", "RC settings copied to front panel.")
        except MSCF16Error as e:
            QMessageBox.critical(self, "Error", f"Failed to copy RC to Panel:\n{str(e)}")

    def copy_panel_to_rc(self):
        """Copy front panel settings to RC"""
        if not self.is_connected:
            QMessageBox.warning(self, "Warning", "Device is not connected.")
            return

        try:
            self.controller.copy_front_panel_to_rc()
            QMessageBox.information(self, "Success", "Front panel settings copied to RC.")
        except MSCF16Error as e:
            QMessageBox.critical(self, "Error", f"Failed to copy Panel to RC:\n{str(e)}")

    def view_settings(self):
        """View all settings (Panel, RC, General) in a new window"""
        if not self.is_connected:
            QMessageBox.warning(self, "Warning", "Device is not connected.")
            return

        try:
            panel_set, rc_set, gen_set = self.controller.display_setup_parsed()

            # Create dialog window
            dialog = QDialog(self)
            dialog.setWindowTitle("Device Settings")
            dialog.setMinimumSize(600, 700)

            # Create scroll area for content
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)

            # Create content widget
            content_widget = QWidget()
            content_layout = QVBoxLayout()
            content_layout.setSpacing(10)

            # Panel Settings
            panel_group = QGroupBox("Panel Settings")
            panel_layout = QVBoxLayout()
            panel_text = self._format_settings_dict(panel_set)
            panel_label = QLabel(panel_text)
            panel_label.setWordWrap(True)
            panel_layout.addWidget(panel_label)
            panel_group.setLayout(panel_layout)
            content_layout.addWidget(panel_group)

            # RC Settings
            rc_group = QGroupBox("RC Settings")
            rc_layout = QVBoxLayout()
            rc_text = self._format_settings_dict(rc_set)
            rc_label = QLabel(rc_text)
            rc_label.setWordWrap(True)
            rc_layout.addWidget(rc_label)
            rc_group.setLayout(rc_layout)
            content_layout.addWidget(rc_group)

            # General Settings
            gen_group = QGroupBox("General Settings")
            gen_layout = QVBoxLayout()
            gen_text = self._format_settings_dict(gen_set)
            gen_label = QLabel(gen_text)
            gen_label.setWordWrap(True)
            gen_layout.addWidget(gen_label)
            gen_group.setLayout(gen_layout)
            content_layout.addWidget(gen_group)

            content_layout.addStretch()
            content_widget.setLayout(content_layout)
            scroll.setWidget(content_widget)

            # Dialog layout
            dialog_layout = QVBoxLayout()
            dialog_layout.addWidget(scroll)

            close_btn = QPushButton("Close")
            close_btn.clicked.connect(dialog.accept)
            dialog_layout.addWidget(close_btn)

            dialog.setLayout(dialog_layout)
            dialog.exec_()

        except MSCF16Error as e:
            QMessageBox.critical(self, "Error", f"Failed to load settings:\n{str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Unexpected error loading settings:\n{str(e)}")

    def _format_settings_dict(self, settings_dict):
        """Format settings dictionary into readable text"""
        if not settings_dict:
            return "No settings available"

        lines = []
        for key, value in settings_dict.items():
            if isinstance(value, list):
                # Format list values
                if len(value) <= 20:
                    formatted = ", ".join(str(v) for v in value)
                    lines.append(f"{key}: [{formatted}]")
                else:
                    formatted = ", ".join(str(v) for v in value[:20])
                    lines.append(f"{key}: [{formatted}... ({len(value)} total)]")
            elif isinstance(value, dict):
                # Format nested dictionary
                formatted = ", ".join(f"{k}: {v}" for k, v in value.items())
                lines.append(f"{key}: {{{formatted}}}")
            else:
                lines.append(f"{key}: {value}")

        return "\n".join(lines)

    def load_rc_settings(self):
        """Load RC settings from device and update GUI"""
        if not self.is_connected:
            QMessageBox.warning(self, "Warning", "Device is not connected.")
            return

        try:
            panel_set, rc_set, gen_set = self.controller.display_setup_parsed()

            # Block signals to prevent triggering set commands during loading
            self._block_all_signals(True)

            # Load threshold values
            if "threshs" in rc_set:
                threshs = rc_set["threshs"]
                for i, value in enumerate(threshs[:16], 1):
                    if i in self.control_panel.threshold_spins:
                        self.control_panel.threshold_spins[i].setValue(value)
                if len(threshs) > 16:
                    self.control_panel.common_threshold_spin.setValue(threshs[-1])

            # Load PZ values
            if "pz" in rc_set:
                pz_values = rc_set["pz"]
                for i, value in enumerate(pz_values[:16], 1):
                    if i in self.control_panel.pz_spins:
                        self.control_panel.pz_spins[i].setValue(value)
                if len(pz_values) > 16:
                    self.control_panel.common_pz_spin.setValue(pz_values[-1])

            # Load shaping times
            if "shts" in rc_set:
                shts = rc_set["shts"]
                for i, value in enumerate(shts[:4], 1):
                    if i in self.control_panel.shaping_spins:
                        self.control_panel.shaping_spins[i].setValue(value)
                if len(shts) > 4:
                    self.control_panel.common_shaping_spin.setValue(shts[-1])

            # Load gains
            if "gains" in rc_set:
                gains = rc_set["gains"]
                for i, value in enumerate(gains[:4], 1):
                    if i in self.control_panel.gain_spins:
                        self.control_panel.gain_spins[i].setValue(value)
                if len(gains) > 4:
                    self.control_panel.common_gain_spin.setValue(gains[-1])

            # Load monitor channel
            if "monitor" in rc_set:
                monitor_ch = rc_set["monitor"]
                if 1 <= monitor_ch <= 16:
                    self.control_panel.monitor_combo.blockSignals(True)
                    self.control_panel.monitor_combo.setCurrentIndex(monitor_ch - 1)
                    self.control_panel.monitor_combo.blockSignals(False)

            # Load multiplicity
            if "mult" in rc_set:
                mult = rc_set["mult"]
                if "high" in mult:
                    self.control_panel.multiplicity_hi_spin.setValue(mult["high"])
                if "low" in mult:
                    self.control_panel.multiplicity_lo_spin.setValue(mult["low"])

            # Load mode settings
            if "single_mode" in rc_set:
                self.single_channel_check.setChecked(rc_set["single_mode"])
            if "ecl_delay" in rc_set:
                self.ecl_delay_check.setChecked(rc_set["ecl_delay"])
            if "blr_active" in rc_set:
                self.blr_mode_check.setChecked(rc_set["blr_active"])
            if "rc_mode" in rc_set:
                self.rc_mode_check.setChecked(rc_set["rc_mode"])

            # Load general settings (coincidence window)
            if "coincidence_time" in gen_set:
                self.control_panel.coincidence_spin.setValue(gen_set["coincidence_time"])

            # Load BLR threshold
            if "blr_thresh" in gen_set:
                self.control_panel.blr_threshold_spin.setValue(gen_set["blr_thresh"])

            # Load timing filter integration time from rc_set
            if "tf_int" in rc_set:
                tf_int_value = rc_set["tf_int"]
                if 0 <= tf_int_value <= 3:
                    self.control_panel.timing_filter_combo.blockSignals(True)
                    self.control_panel.timing_filter_combo.setCurrentIndex(tf_int_value)
                    self.control_panel.timing_filter_combo.blockSignals(False)

            # Unblock signals
            self._block_all_signals(False)

            QMessageBox.information(self, "Success", "RC settings loaded to GUI.")

        except MSCF16Error as e:
            self._block_all_signals(False)
            QMessageBox.critical(self, "Error", f"Failed to load RC settings:\n{str(e)}")
        except Exception as e:
            self._block_all_signals(False)
            QMessageBox.critical(self, "Error", f"Unexpected error loading settings:\n{str(e)}")

    def _block_all_signals(self, block):
        """Block or unblock all signal emissions"""
        # Block threshold spins
        for spin in self.control_panel.threshold_spins.values():
            spin.blockSignals(block)
        self.control_panel.common_threshold_spin.blockSignals(block)

        # Block PZ spins
        for spin in self.control_panel.pz_spins.values():
            spin.blockSignals(block)
        self.control_panel.common_pz_spin.blockSignals(block)

        # Block shaping time spins
        for spin in self.control_panel.shaping_spins.values():
            spin.blockSignals(block)
        self.control_panel.common_shaping_spin.blockSignals(block)

        # Block gain spins
        for spin in self.control_panel.gain_spins.values():
            spin.blockSignals(block)
        self.control_panel.common_gain_spin.blockSignals(block)

        # Block mode checkboxes
        self.single_channel_check.blockSignals(block)
        self.ecl_delay_check.blockSignals(block)
        self.blr_mode_check.blockSignals(block)
        self.rc_mode_check.blockSignals(block)

        # Block general settings spins
        self.control_panel.multiplicity_hi_spin.blockSignals(block)
        self.control_panel.multiplicity_lo_spin.blockSignals(block)
        self.control_panel.coincidence_spin.blockSignals(block)
        self.control_panel.blr_threshold_spin.blockSignals(block)
        self.control_panel.timing_filter_combo.blockSignals(block)


class MSCF16MainWindow(QMainWindow):
    """MSCF-16 Main Window"""

    def __init__(self, auto_connect_port=None, auto_connect_baudrate=9600):
        super().__init__()
        self.auto_connect_port = auto_connect_port
        self.auto_connect_baudrate = auto_connect_baudrate
        self.device_tabs = []  # List to track device tabs
        self.init_ui()
        # Auto-connect if port is provided (after UI is initialized)
        if auto_connect_port:
            QTimer.singleShot(200, self.auto_connect_device)

    def init_ui(self):
        self.setWindowTitle("MSCF-16 NIM Device Controller")
        self.setGeometry(100, 100, 1000, 700)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setSpacing(2)
        main_layout.setContentsMargins(2, 2, 2, 2)

        # Connection panel (outside tabs)
        self.connection_panel = ConnectionPanel()
        self.connection_panel.connection_success.connect(self.on_device_connected)
        main_layout.addWidget(self.connection_panel)

        # Tab widget for multiple devices
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        main_layout.addWidget(self.tab_widget)

        central_widget.setLayout(main_layout)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

    def on_device_connected(self, controller, port, baudrate):
        """Called when a device is successfully connected"""
        device_tab = DeviceTab(self, controller, port, baudrate)
        tab_index = self.tab_widget.addTab(device_tab, port)
        self.device_tabs.append(device_tab)
        self.tab_widget.setCurrentIndex(tab_index)
        self.status_bar.showMessage(f"Device connected: {port}")

    def add_new_device_tab(self):
        """Add a new device tab (for auto-connect)"""
        # This should not be called directly anymore
        pass

    def close_tab(self, index):
        """Close a device tab"""
        if index < 0 or index >= len(self.device_tabs):
            return

        device_tab = self.device_tabs[index]

        # Disconnect device if connected
        if device_tab.is_connected and device_tab.controller:
            try:
                device_tab.controller.disconnect()
            except:
                pass

        # Remove tab
        self.tab_widget.removeTab(index)
        self.device_tabs.pop(index)

    def close_tab_by_widget(self, device_tab):
        """Close a tab by its widget reference"""
        if device_tab in self.device_tabs:
            index = self.device_tabs.index(device_tab)
            self.close_tab(index)

    def update_tab_title(self, device_tab, title):
        """Update the title of a device tab"""
        if device_tab in self.device_tabs:
            index = self.device_tabs.index(device_tab)
            self.tab_widget.setTabText(index, title)
            self.status_bar.showMessage(f"Device {title} connected")

    def auto_connect_device(self):
        """Auto-connect to device using provided port"""
        if not self.auto_connect_port:
            return

        try:
            # Refresh ports first to get available ports
            self.connection_panel.refresh_ports()

            # Try to find the port in the combo box
            port_found = False
            for i in range(self.connection_panel.port_combo.count()):
                port_text = self.connection_panel.port_combo.itemText(i)
                if self.auto_connect_port in port_text:
                    self.connection_panel.port_combo.setCurrentIndex(i)
                    port_found = True
                    break

            # If port not found in list, add it manually
            if not port_found:
                port_text = f"{self.auto_connect_port} - Auto"
                self.connection_panel.port_combo.addItem(port_text)
                self.connection_panel.port_combo.setCurrentText(port_text)

            # Set baudrate if provided
            if self.auto_connect_baudrate:
                baudrate_str = str(self.auto_connect_baudrate)
                if baudrate_str in [self.connection_panel.baudrate_combo.itemText(i) for i in range(self.connection_panel.baudrate_combo.count())]:
                    self.connection_panel.baudrate_combo.setCurrentText(baudrate_str)

            # Connect
            self.connection_panel.connect_device()
        except Exception as e:
            QMessageBox.critical(self, "Connection Error",
                               f"Failed to auto-connect to {self.auto_connect_port}:\n{str(e)}")

    def closeEvent(self, event):
        """Called when window is closed"""
        # Check if any device is connected
        connected_devices = [tab for tab in self.device_tabs if tab.is_connected and tab.controller]

        if connected_devices:
            reply = QMessageBox.question(self, 'Exit Confirmation',
                                       f'{len(connected_devices)} device(s) are connected. Are you sure you want to exit?',
                                       QMessageBox.Yes | QMessageBox.No,
                                       QMessageBox.No)

            if reply == QMessageBox.Yes:
                # Disconnect all devices
                for tab in connected_devices:
                    try:
                        tab.controller.disconnect()
                    except:
                        pass
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

    # Parse command line arguments for auto-connect
    auto_connect_port = None
    auto_connect_baudrate = 9600
    if len(sys.argv) > 1:
        auto_connect_port = sys.argv[1]
        print(f"Auto-connecting to device at: {auto_connect_port}")
        if len(sys.argv) > 2:
            try:
                auto_connect_baudrate = int(sys.argv[2])
                print(f"Baud rate: {auto_connect_baudrate}")
            except ValueError:
                print(f"Warning: Invalid baud rate '{sys.argv[2]}', using default 9600")

    # Create and show main window
    window = MSCF16MainWindow(auto_connect_port=auto_connect_port,
                             auto_connect_baudrate=auto_connect_baudrate)
    window.show()

    # Start event loop
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
