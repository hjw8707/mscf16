// MHV-4 Web Client Application

let socket;
let modules = {};
let currentModuleId = null;

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    initializeSocket();
    initializeConnectionPanel();
    initializeModuleManagement();
    loadPorts();
});

// Socket.IO initialization
function initializeSocket() {
    socket = io();

    socket.on('connect', function() {
        console.log('Connected to server');
    });

    socket.on('connected', function(data) {
        console.log('Server message:', data.message);
    });

    socket.on('readings_update', function(data) {
        updateModuleReadings(data.device_id, data.readings);
    });

    socket.on('initial_values', function(data) {
        updateInitialValues(data.device_id, data);
    });

    socket.on('device_disconnected', function(data) {
        removeModule(data.device_id);
    });
}

// Connection Panel
function initializeConnectionPanel() {
    document.getElementById('refresh-btn').addEventListener('click', loadPorts);
    document.getElementById('connect-btn').addEventListener('click', toggleConnection);
}

async function loadPorts() {
    try {
        const response = await fetch('/api/ports');
        const ports = await response.json();

        const select = document.getElementById('port-select');
        select.innerHTML = '';

        if (ports.length === 0) {
            select.innerHTML = '<option value="">No available ports</option>';
        } else {
            ports.forEach(port => {
                const option = document.createElement('option');
                option.value = port.device;
                option.textContent = `${port.device} - ${port.description}`;
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Error loading ports:', error);
        alert('Failed to load ports');
    }
}

async function toggleConnection() {
    const portSelect = document.getElementById('port-select');
    const port = portSelect.value;
    const connectBtn = document.getElementById('connect-btn');
    const statusLabel = document.getElementById('connection-status');

    if (!port || port.includes('No available')) {
        alert('Please select a valid port');
        return;
    }

    if (connectBtn.textContent === 'Connect') {
        await connectDevice(port);
    } else {
        // Disconnect current device
        if (currentModuleId) {
            await disconnectDevice(currentModuleId);
        }
    }
}

async function connectDevice(port) {
    try {
        const response = await fetch('/api/connect', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                port: port,
                device_id: port
            })
        });

        const result = await response.json();

        if (result.success) {
            addModule(result.device_id, port);
            document.getElementById('connect-btn').textContent = 'Disconnect';
            document.getElementById('connection-status').textContent = 'Connected';
            document.getElementById('connection-status').className = 'status-connected';
            document.getElementById('port-select').disabled = true;
        } else {
            alert(`Connection failed: ${result.error}`);
        }
    } catch (error) {
        console.error('Error connecting:', error);
        alert('Failed to connect to device');
    }
}

async function disconnectDevice(deviceId) {
    try {
        const response = await fetch(`/api/disconnect/${deviceId}`, {
            method: 'POST'
        });

        const result = await response.json();

        if (result.success) {
            document.getElementById('connect-btn').textContent = 'Connect';
            document.getElementById('connection-status').textContent = 'Not Connected';
            document.getElementById('connection-status').className = 'status-not-connected';
            document.getElementById('port-select').disabled = false;
        } else {
            alert(`Disconnect failed: ${result.error}`);
        }
    } catch (error) {
        console.error('Error disconnecting:', error);
        alert('Failed to disconnect from device');
    }
}

// Module Management
function initializeModuleManagement() {
    document.getElementById('add-module-btn').addEventListener('click', function() {
        // For now, use connection panel
        alert('Use Connection Settings to add a module');
    });

    document.getElementById('remove-module-btn').addEventListener('click', function() {
        if (currentModuleId) {
            if (confirm(`Remove module ${currentModuleId}?`)) {
                disconnectDevice(currentModuleId);
            }
        } else {
            alert('No module selected');
        }
    });
}

// Module UI
function addModule(deviceId, port) {
    if (modules[deviceId]) {
        return; // Module already exists
    }

    const tabsContainer = document.getElementById('module-tabs');

    // Create tab header if not exists
    if (!document.querySelector('.tab-header')) {
        const tabHeader = document.createElement('div');
        tabHeader.className = 'tab-header';
        tabsContainer.insertBefore(tabHeader, tabsContainer.firstChild);
    }

    const tabHeader = document.querySelector('.tab-header');

    // Create tab button
    const tabButton = document.createElement('button');
    tabButton.className = 'tab-button';
    tabButton.textContent = `Module ${Object.keys(modules).length + 1}`;
    tabButton.addEventListener('click', () => switchModule(deviceId));
    tabHeader.appendChild(tabButton);

    // Create tab content
    const tabContent = document.createElement('div');
    tabContent.className = 'tab-content';
    tabContent.id = `module-${deviceId}`;
    tabContent.innerHTML = createModulePanel(deviceId);
    tabsContainer.appendChild(tabContent);

    // Initialize module
    modules[deviceId] = {
        deviceId: deviceId,
        port: port,
        tabButton: tabButton,
        tabContent: tabContent
    };

    // Switch to this module
    switchModule(deviceId);

    // Initialize channel controls
    initializeChannelControls(deviceId);
}

function createModulePanel(deviceId) {
    return `
        <div class="module-panel" data-device-id="${deviceId}">
            <div class="module-header">
                <div class="ramp-speed-control">
                    <label>Ramp Speed:</label>
                    <select id="ramp-speed-${deviceId}" class="ramp-speed-select">
                        <option value="0">5 V/s</option>
                        <option value="1" selected>25 V/s</option>
                        <option value="2">100 V/s</option>
                        <option value="3">500 V/s</option>
                    </select>
                </div>
            </div>
            <div class="channels-grid">
                ${createChannelPanel(deviceId, 0)}
                ${createChannelPanel(deviceId, 1)}
                ${createChannelPanel(deviceId, 2)}
                ${createChannelPanel(deviceId, 3)}
            </div>
        </div>
    `;
}

function createChannelPanel(deviceId, channelNum) {
    return `
        <div class="channel-panel" data-device-id="${deviceId}" data-channel="${channelNum}">
            <div class="channel-header">
                <span class="channel-label">HV ${channelNum}</span>
                <div class="polarity-controls">
                    <div class="polarity-select">
                        <label>Polarity:</label>
                        <select class="polarity-combo" data-channel="${channelNum}">
                            <option value="p">+</option>
                            <option value="n">-</option>
                        </select>
                    </div>
                    <div class="polarity-indicators">
                        <div class="polarity-indicator polarity-positive active" data-pole="+">+</div>
                        <div class="polarity-indicator polarity-negative inactive" data-pole="-">-</div>
                    </div>
                    <div class="power-indicator power-off" data-channel="${channelNum}">OFF</div>
                </div>
            </div>

            <div class="display-container">
                <div class="display-item">
                    <div class="display-label">Voltage (V)</div>
                    <div class="lcd-display" id="voltage-${deviceId}-${channelNum}">000.0</div>
                </div>
                <div class="display-item">
                    <div class="display-label">Current (μA)</div>
                    <div class="lcd-display" id="current-${deviceId}-${channelNum}">0.000</div>
                </div>
            </div>

            <div class="control-group">
                <div class="control-row">
                    <label>Preset V:</label>
                    <input type="number" class="voltage-preset-input" data-channel="${channelNum}" min="0" max="800" step="0.1" value="0">
                    <span>V</span>
                    <button class="set-voltage-btn" data-channel="${channelNum}">Set</button>
                </div>
                <div class="control-row">
                    <label>Limit V:</label>
                    <input type="number" class="voltage-limit-input" data-channel="${channelNum}" min="0" max="800" step="0.1" value="800">
                    <span>V</span>
                    <button class="set-voltage-limit-btn" data-channel="${channelNum}">Set</button>
                </div>
                <div class="control-row">
                    <label>Limit I:</label>
                    <input type="number" class="current-limit-input" data-channel="${channelNum}" min="0" max="20000" step="0.1" value="0">
                    <span>μA</span>
                    <button class="set-current-limit-btn" data-channel="${channelNum}">Set</button>
                </div>
            </div>

            <div class="ramp-group">
                <h3>Custom Ramping</h3>
                <div class="ramp-checkbox">
                    <input type="checkbox" class="custom-ramp-checkbox" data-channel="${channelNum}" id="ramp-${deviceId}-${channelNum}">
                    <label for="ramp-${deviceId}-${channelNum}">Enable Custom Ramping</label>
                </div>
                <div class="step-interval-row">
                    <label>Step:</label>
                    <input type="number" class="voltage-step-input" data-channel="${channelNum}" min="0.1" max="100" step="0.1" value="1.0">
                    <span>V</span>
                    <label>Interval:</label>
                    <input type="number" class="time-interval-input" data-channel="${channelNum}" min="1" max="60" step="1" value="1">
                    <span>s</span>
                </div>
                <div class="ramp-status">
                    <div class="ramp-status-indicator" data-channel="${channelNum}"></div>
                    <span class="ramp-status-label" data-channel="${channelNum}">Stopped</span>
                    <button class="stop-ramp-btn" data-channel="${channelNum}">Stop Ramping</button>
                </div>
            </div>

            <div class="auto-shutdown">
                <input type="checkbox" class="auto-shutdown-checkbox" data-channel="${channelNum}" id="auto-${deviceId}-${channelNum}">
                <label for="auto-${deviceId}-${channelNum}">Auto Shutdown</label>
            </div>

            <div class="power-controls">
                <button class="power-btn power-on-btn" data-channel="${channelNum}">ON</button>
                <button class="power-btn power-off-btn" data-channel="${channelNum}">OFF</button>
            </div>

            <div class="temp-comp-group">
                <h3>Temperature Compensation</h3>
                <div class="temp-comp-row">
                    <label>NTC:</label>
                    <select class="ntc-combo" data-channel="${channelNum}">
                        <option value="0">Off</option>
                        <option value="1">NTC0</option>
                        <option value="2">NTC1</option>
                        <option value="3">NTC2</option>
                        <option value="4">NTC3</option>
                    </select>
                </div>
                <div class="temp-comp-row">
                    <label>Ref Temp:</label>
                    <input type="number" class="ref-temp-input" data-channel="${channelNum}" min="-50" max="150" step="0.1" value="28.5">
                    <span>(0.1°C)</span>
                </div>
                <div class="temp-comp-row">
                    <label>Slope:</label>
                    <input type="number" class="slope-input" data-channel="${channelNum}" min="-10000" max="10000" step="1" value="800">
                    <span>(mV/°C)</span>
                </div>
            </div>
        </div>
    `;
}

function initializeChannelControls(deviceId) {
    const modulePanel = document.querySelector(`.module-panel[data-device-id="${deviceId}"]`);
    if (!modulePanel) return;

    // Ramp speed
    const rampSpeedSelect = modulePanel.querySelector(`#ramp-speed-${deviceId}`);
    if (rampSpeedSelect) {
        rampSpeedSelect.addEventListener('change', function() {
            sendCommand(deviceId, 'set_ramp_speed', {
                ramp_speed_index: parseInt(this.value)
            });
        });
    }

    // Channel controls
    for (let ch = 0; ch < 4; ch++) {
        const channelPanel = modulePanel.querySelector(`.channel-panel[data-channel="${ch}"]`);
        if (!channelPanel) continue;

        // Polarity
        const polarityCombo = channelPanel.querySelector('.polarity-combo');
        if (polarityCombo) {
            polarityCombo.addEventListener('change', function() {
                sendCommand(deviceId, 'set_polarity', {
                    channel: ch,
                    polarity: this.value
                });
            });
        }

        // Voltage preset
        const voltagePresetBtn = channelPanel.querySelector('.set-voltage-btn');
        if (voltagePresetBtn) {
            voltagePresetBtn.addEventListener('click', function() {
                const input = channelPanel.querySelector('.voltage-preset-input');
                sendCommand(deviceId, 'set_voltage', {
                    channel: ch,
                    voltage: parseFloat(input.value)
                });
            });
        }

        // Voltage limit
        const voltageLimitBtn = channelPanel.querySelector('.set-voltage-limit-btn');
        if (voltageLimitBtn) {
            voltageLimitBtn.addEventListener('click', function() {
                const input = channelPanel.querySelector('.voltage-limit-input');
                sendCommand(deviceId, 'set_voltage_limit', {
                    channel: ch,
                    voltage_limit: parseFloat(input.value)
                });
            });
        }

        // Current limit
        const currentLimitBtn = channelPanel.querySelector('.set-current-limit-btn');
        if (currentLimitBtn) {
            currentLimitBtn.addEventListener('click', function() {
                const input = channelPanel.querySelector('.current-limit-input');
                sendCommand(deviceId, 'set_current_limit', {
                    channel: ch,
                    current_limit: parseFloat(input.value)
                });
            });
        }

        // Power buttons
        const onBtn = channelPanel.querySelector('.power-on-btn');
        const offBtn = channelPanel.querySelector('.power-off-btn');
        if (onBtn) {
            onBtn.addEventListener('click', function() {
                sendCommand(deviceId, 'turn_on', { channel: ch });
            });
        }
        if (offBtn) {
            offBtn.addEventListener('click', function() {
                sendCommand(deviceId, 'turn_off', { channel: ch });
            });
        }

        // Auto shutdown
        const autoShutdownCheckbox = channelPanel.querySelector('.auto-shutdown-checkbox');
        if (autoShutdownCheckbox) {
            autoShutdownCheckbox.addEventListener('change', function() {
                sendCommand(deviceId, 'set_auto_shutdown', {
                    channel: ch,
                    enable: this.checked
                });
            });
        }

        // NTC
        const ntcCombo = channelPanel.querySelector('.ntc-combo');
        if (ntcCombo) {
            ntcCombo.addEventListener('change', function() {
                const ntcChannel = this.value === '0' ? null : parseInt(this.value) - 1;
                sendCommand(deviceId, 'set_temperature_compensation', {
                    channel: ch,
                    ntc_channel: ntcChannel
                });
            });
        }

        // Reference temperature
        const refTempInput = channelPanel.querySelector('.ref-temp-input');
        if (refTempInput) {
            refTempInput.addEventListener('change', function() {
                sendCommand(deviceId, 'set_reference_temperature', {
                    channel: ch,
                    temperature: parseFloat(this.value)
                });
            });
        }

        // Slope
        const slopeInput = channelPanel.querySelector('.slope-input');
        if (slopeInput) {
            slopeInput.addEventListener('change', function() {
                sendCommand(deviceId, 'set_temperature_slope', {
                    channel: ch,
                    slope: parseInt(this.value)
                });
            });
        }
    }
}

function switchModule(deviceId) {
    // Hide all tab contents
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });

    // Remove active class from all tab buttons
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active');
    });

    // Show selected tab content
    const tabContent = document.getElementById(`module-${deviceId}`);
    if (tabContent) {
        tabContent.classList.add('active');
    }

    // Activate selected tab button
    if (modules[deviceId] && modules[deviceId].tabButton) {
        modules[deviceId].tabButton.classList.add('active');
    }

    currentModuleId = deviceId;
}

function removeModule(deviceId) {
    if (modules[deviceId]) {
        // Remove tab button
        if (modules[deviceId].tabButton) {
            modules[deviceId].tabButton.remove();
        }

        // Remove tab content
        if (modules[deviceId].tabContent) {
            modules[deviceId].tabContent.remove();
        }

        delete modules[deviceId];

        // Switch to first available module
        const remainingIds = Object.keys(modules);
        if (remainingIds.length > 0) {
            switchModule(remainingIds[0]);
        } else {
            currentModuleId = null;
        }
    }
}

// API Communication
async function sendCommand(deviceId, command, params) {
    try {
        const response = await fetch(`/api/command/${deviceId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                command: command,
                params: params
            })
        });

        const result = await response.json();

        if (!result.success) {
            alert(`Command failed: ${result.error}`);
        }
    } catch (error) {
        console.error('Error sending command:', error);
        alert('Failed to send command');
    }
}

// Update readings
function updateModuleReadings(deviceId, readings) {
    for (let ch = 0; ch < 4; ch++) {
        const voltage = readings[`voltage_${ch}`];
        const current = readings[`current_${ch}`];

        if (voltage !== undefined) {
            const voltageDisplay = document.getElementById(`voltage-${deviceId}-${ch}`);
            if (voltageDisplay) {
                voltageDisplay.textContent = voltage.toFixed(1);
            }
        }

        if (current !== undefined) {
            const currentDisplay = document.getElementById(`current-${deviceId}-${ch}`);
            if (currentDisplay) {
                currentDisplay.textContent = current.toFixed(3);
            }
        }
    }
}

// Update initial values
function updateInitialValues(deviceId, data) {
    const modulePanel = document.querySelector(`.module-panel[data-device-id="${deviceId}"]`);
    if (!modulePanel) return;

    if (data.type === 'ramp_speed') {
        const rampSpeedSelect = modulePanel.querySelector(`#ramp-speed-${deviceId}`);
        if (rampSpeedSelect) {
            rampSpeedSelect.value = data.value;
        }
    } else if (data.channel !== undefined) {
        const channelPanel = modulePanel.querySelector(`.channel-panel[data-channel="${data.channel}"]`);
        if (!channelPanel) return;

        switch (data.type) {
            case 'voltage_preset':
                const voltagePresetInput = channelPanel.querySelector('.voltage-preset-input');
                if (voltagePresetInput) {
                    voltagePresetInput.value = data.value;
                }
                break;
            case 'voltage_limit':
                const voltageLimitInput = channelPanel.querySelector('.voltage-limit-input');
                if (voltageLimitInput) {
                    voltageLimitInput.value = data.value;
                }
                break;
            case 'current_limit':
                const currentLimitInput = channelPanel.querySelector('.current-limit-input');
                if (currentLimitInput) {
                    currentLimitInput.value = data.value;
                }
                break;
            case 'polarity':
                const polarityCombo = channelPanel.querySelector('.polarity-combo');
                if (polarityCombo) {
                    polarityCombo.value = data.value;
                    updatePolarityIndicators(channelPanel, data.value);
                }
                break;
            case 'ntc':
                const ntcCombo = channelPanel.querySelector('.ntc-combo');
                if (ntcCombo) {
                    ntcCombo.value = data.value;
                }
                break;
            case 'ref_temp':
                const refTempInput = channelPanel.querySelector('.ref-temp-input');
                if (refTempInput) {
                    refTempInput.value = data.value;
                }
                break;
            case 'slope':
                const slopeInput = channelPanel.querySelector('.slope-input');
                if (slopeInput) {
                    slopeInput.value = data.value;
                }
                break;
        }
    }
}

function updatePolarityIndicators(channelPanel, polarity) {
    const positiveIndicator = channelPanel.querySelector('.polarity-positive');
    const negativeIndicator = channelPanel.querySelector('.polarity-negative');

    if (polarity === 'p') {
        positiveIndicator.classList.add('active');
        positiveIndicator.classList.remove('inactive');
        negativeIndicator.classList.add('inactive');
        negativeIndicator.classList.remove('active');
    } else {
        negativeIndicator.classList.add('active');
        negativeIndicator.classList.remove('inactive');
        positiveIndicator.classList.add('inactive');
        positiveIndicator.classList.remove('active');
    }
}
