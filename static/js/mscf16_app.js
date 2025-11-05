// MSCF-16 Web Client Application

let socket;
let modules = {};
let currentModuleId = null;

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    initializeSocket();
    initializeConnectionPanel();
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
    const baudrateSelect = document.getElementById('baudrate-select');
    const port = portSelect.value;
    const baudrate = parseInt(baudrateSelect.value);
    const connectBtn = document.getElementById('connect-btn');

    if (!port || port.includes('No available')) {
        alert('Please select a valid port');
        return;
    }

    if (connectBtn.textContent === 'Connect') {
        await connectDevice(port, baudrate);
    } else {
        // Disconnect current device
        if (currentModuleId) {
            await disconnectDevice(currentModuleId);
        }
    }
}

async function connectDevice(port, baudrate) {
    try {
        const response = await fetch('/api/connect', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                port: port,
                baudrate: baudrate,
                device_id: port
            })
        });

        const result = await response.json();

        if (result.success) {
            addModule(result.device_id, port);
            document.getElementById('connect-btn').textContent = 'Disconnect';
            document.getElementById('port-select').disabled = true;
            document.getElementById('baudrate-select').disabled = true;
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
            document.getElementById('port-select').disabled = false;
            document.getElementById('baudrate-select').disabled = false;
        } else {
            alert(`Disconnect failed: ${result.error}`);
        }
    } catch (error) {
        console.error('Error disconnecting:', error);
        alert('Failed to disconnect from device');
    }
}

// Module UI
function addModule(deviceId, port) {
    if (modules[deviceId]) {
        return;
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
    tabButton.textContent = `Device ${Object.keys(modules).length + 1}`;
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

    // Initialize controls
    initializeControls(deviceId);

    // Load version
    sendCommand(deviceId, 'get_version', {});
}

function createModulePanel(deviceId) {
    return `
        <div class="device-tab" data-device-id="${deviceId}">
            <div class="device-header">
                <div class="version-info">
                    <span class="version-label">Version:</span>
                    <span class="version-value" id="version-${deviceId}">Loading...</span>
                    <button class="disconnect-btn" onclick="disconnectDevice('${deviceId}')">Disconnect</button>
                </div>
                <div class="action-buttons">
                    <button class="action-btn" onclick="viewSettings('${deviceId}')">View Setting</button>
                    <button class="action-btn" onclick="loadRCSettings('${deviceId}')">Load RC Setting</button>
                    <button class="action-btn" onclick="copyRCToPanel('${deviceId}')">RC→Panel</button>
                    <button class="action-btn" onclick="copyPanelToRC('${deviceId}')">Panel→RC</button>
                </div>
                <div class="mode-controls">
                    <label class="mode-checkbox">
                        <input type="checkbox" class="mode-checkbox-input" id="single-mode-${deviceId}" data-mode="single_mode">
                        Single Mode
                    </label>
                    <label class="mode-checkbox">
                        <input type="checkbox" class="mode-checkbox-input" id="ecl-delay-${deviceId}" data-mode="ecl_delay">
                        ECL Delay
                    </label>
                    <label class="mode-checkbox">
                        <input type="checkbox" class="mode-checkbox-input" id="blr-mode-${deviceId}" data-mode="blr_mode" checked>
                        BLR Mode
                    </label>
                    <label class="mode-checkbox">
                        <input type="checkbox" class="mode-checkbox-input" id="rc-mode-${deviceId}" data-mode="rc_mode">
                        RC Mode
                    </label>
                </div>
            </div>

            <div class="control-panel">
                <div class="channel-control">
                    ${createThresholdSection(deviceId)}
                    ${createPZSection(deviceId)}
                    ${createMonitorSection(deviceId)}
                    ${createAutoPZSection(deviceId)}
                </div>
                <div class="group-control">
                    ${createShapingTimeSection(deviceId)}
                    ${createGainSection(deviceId)}
                </div>
            </div>

            ${createGeneralSettings(deviceId)}
        </div>
    `;
}

function createThresholdSection(deviceId) {
    let html = '<div class="control-section"><div class="section-title">Threshold Settings</div><div class="threshold-grid">';
    for (let ch = 1; ch <= 16; ch++) {
        html += `
            <div class="threshold-item">
                <span class="threshold-label">CH${ch.toString().padStart(2, '0')}</span>
                <input type="number" class="threshold-input" id="thresh-${deviceId}-${ch}" min="0" max="255" value="128" data-channel="${ch}">
                <button class="threshold-btn" onclick="setThreshold('${deviceId}', ${ch})">Set</button>
            </div>
        `;
    }
    html += '</div>';
    html += `
        <div class="common-threshold">
            <label>Common:</label>
            <input type="number" class="threshold-input" id="thresh-common-${deviceId}" min="0" max="255" value="128">
            <button class="common-threshold-btn" onclick="setThreshold('${deviceId}', 17)">Apply to All Channels</button>
        </div>
    `;
    html += '</div>';
    return html;
}

function createPZSection(deviceId) {
    let html = '<div class="control-section"><div class="section-title">PZ Value Settings</div><div class="pz-grid">';
    for (let ch = 1; ch <= 16; ch++) {
        html += `
            <div class="pz-item">
                <span class="pz-label">CH${ch.toString().padStart(2, '0')}</span>
                <input type="number" class="pz-input" id="pz-${deviceId}-${ch}" min="0" max="255" value="100" data-channel="${ch}">
                <button class="pz-btn" onclick="setPZ('${deviceId}', ${ch})">Set</button>
            </div>
        `;
    }
    html += '</div>';
    html += `
        <div class="common-pz">
            <label>Common:</label>
            <input type="number" class="pz-input" id="pz-common-${deviceId}" min="0" max="255" value="100">
            <button class="common-pz-btn" onclick="setPZ('${deviceId}', 17)">Apply to All Channels</button>
        </div>
    `;
    html += '</div>';
    return html;
}

function createMonitorSection(deviceId) {
    let options = '';
    for (let ch = 1; ch <= 16; ch++) {
        options += `<option value="${ch}">CH${ch.toString().padStart(2, '0')}</option>`;
    }
    return `
        <div class="control-section">
            <div class="monitor-group">
                <div class="section-title">Monitor Channel Settings</div>
                <div class="monitor-row">
                    <label>Monitor Channel:</label>
                    <select class="monitor-select" id="monitor-${deviceId}" onchange="setMonitorChannel('${deviceId}', this.value)">
                        ${options}
                    </select>
                </div>
            </div>
        </div>
    `;
}

function createAutoPZSection(deviceId) {
    let options = '<option value="0">All</option>';
    for (let ch = 1; ch <= 16; ch++) {
        options += `<option value="${ch}">CH${ch.toString().padStart(2, '0')}</option>`;
    }
    return `
        <div class="control-section">
            <div class="auto-pz-group">
                <div class="section-title">Automatic PZ Settings</div>
                <div class="auto-pz-row">
                    <label>Channel:</label>
                    <select class="auto-pz-select" id="auto-pz-${deviceId}">
                        ${options}
                    </select>
                    <button class="auto-pz-btn" onclick="setAutomaticPZ('${deviceId}')">Set</button>
                </div>
            </div>
        </div>
    `;
}

function createShapingTimeSection(deviceId) {
    let html = '<div class="group-settings"><div class="shaping-group"><div class="section-title">Shaping Time Settings</div>';
    for (let g = 1; g <= 4; g++) {
        html += `
            <div class="shaping-row">
                <label>G${g}:</label>
                <input type="number" class="shaping-input" id="shaping-${deviceId}-${g}" min="0" max="15" value="8" data-group="${g}">
                <button class="shaping-btn" onclick="setShapingTime('${deviceId}', ${g})">Set</button>
            </div>
        `;
    }
    html += `
        <div class="common-shaping">
            <label>Common:</label>
            <input type="number" class="shaping-input" id="shaping-common-${deviceId}" min="0" max="15" value="8">
            <button class="common-shaping-btn" onclick="setShapingTime('${deviceId}', 5)">Apply to All Groups</button>
        </div>
    `;
    html += '</div></div>';
    return html;
}

function createGainSection(deviceId) {
    let html = '<div class="gain-group"><div class="section-title">Gain Settings</div>';
    for (let g = 1; g <= 4; g++) {
        html += `
            <div class="gain-row">
                <label>G${g}:</label>
                <input type="number" class="gain-input" id="gain-${deviceId}-${g}" min="0" max="15" value="8" data-group="${g}">
                <button class="gain-btn" onclick="setGain('${deviceId}', ${g})">Set</button>
            </div>
        `;
    }
    html += `
        <div class="common-gain">
            <label>Common:</label>
            <input type="number" class="gain-input" id="gain-common-${deviceId}" min="0" max="15" value="8">
            <button class="common-gain-btn" onclick="setGain('${deviceId}', 5)">Apply to All Groups</button>
        </div>
    `;
    html += '</div>';
    return html;
}

function createGeneralSettings(deviceId) {
    return `
        <div class="general-settings">
            <div class="section-title">General Settings</div>
            <div class="general-row">
                <label>Coincidence Window:</label>
                <input type="number" class="general-input" id="coincidence-${deviceId}" min="0" max="255" value="128">
                <button class="general-btn" onclick="setCoincidenceWindow('${deviceId}')">Set</button>

                <label>Shaper Offset:</label>
                <input type="number" class="general-input" id="shaper-offset-${deviceId}" min="0" max="200" value="100">
                <button class="general-btn" onclick="setShaperOffset('${deviceId}')">Set</button>

                <label>Threshold Offset:</label>
                <input type="number" class="general-input" id="threshold-offset-${deviceId}" min="0" max="200" value="100">
                <button class="general-btn" onclick="setThresholdOffset('${deviceId}')">Set</button>

                <label>BLR Threshold:</label>
                <input type="number" class="general-input" id="blr-threshold-${deviceId}" min="0" max="255" value="128">
                <button class="general-btn" onclick="setBLRThreshold('${deviceId}')">Set</button>
            </div>
            <div class="general-row">
                <label>Multiplicity High:</label>
                <input type="number" class="general-input" id="mult-hi-${deviceId}" min="1" max="9" value="5">
                <label>Low:</label>
                <input type="number" class="general-input" id="mult-lo-${deviceId}" min="1" max="8" value="2">
                <button class="general-btn" onclick="setMultiplicity('${deviceId}')">Set</button>

                <label>Timing Filter Int. Time:</label>
                <select class="general-select" id="timing-filter-${deviceId}" onchange="setTimingFilter('${deviceId}', this.value)">
                    <option value="0">0</option>
                    <option value="1">1</option>
                    <option value="2">2</option>
                    <option value="3">3</option>
                </select>
            </div>
        </div>
    `;
}

function initializeControls(deviceId) {
    // Mode checkboxes
    document.querySelectorAll(`#single-mode-${deviceId}, #ecl-delay-${deviceId}, #blr-mode-${deviceId}, #rc-mode-${deviceId}`).forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const mode = this.dataset.mode;
            sendCommand(deviceId, `set_${mode}`, { enable: this.checked });
        });
    });
}

function switchModule(deviceId) {
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });

    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active');
    });

    const tabContent = document.getElementById(`module-${deviceId}`);
    if (tabContent) {
        tabContent.classList.add('active');
    }

    if (modules[deviceId] && modules[deviceId].tabButton) {
        modules[deviceId].tabButton.classList.add('active');
    }

    currentModuleId = deviceId;
}

function removeModule(deviceId) {
    if (modules[deviceId]) {
        if (modules[deviceId].tabButton) {
            modules[deviceId].tabButton.remove();
        }
        if (modules[deviceId].tabContent) {
            modules[deviceId].tabContent.remove();
        }
        delete modules[deviceId];

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

// Command functions
function setThreshold(deviceId, channel) {
    const input = channel === 17
        ? document.getElementById(`thresh-common-${deviceId}`)
        : document.getElementById(`thresh-${deviceId}-${channel}`);
    sendCommand(deviceId, 'set_threshold', { channel: channel, value: parseInt(input.value) });
}

function setPZ(deviceId, channel) {
    const input = channel === 17
        ? document.getElementById(`pz-common-${deviceId}`)
        : document.getElementById(`pz-${deviceId}-${channel}`);
    sendCommand(deviceId, 'set_pz_value', { channel: channel, value: parseInt(input.value) });
}

function setMonitorChannel(deviceId, channel) {
    sendCommand(deviceId, 'set_monitor_channel', { channel: parseInt(channel) });
}

function setAutomaticPZ(deviceId) {
    const select = document.getElementById(`auto-pz-${deviceId}`);
    const channel = parseInt(select.value);
    sendCommand(deviceId, 'set_automatic_pz', { channel: channel === 0 ? null : channel });
}

function setShapingTime(deviceId, group) {
    const input = group === 5
        ? document.getElementById(`shaping-common-${deviceId}`)
        : document.getElementById(`shaping-${deviceId}-${group}`);
    sendCommand(deviceId, 'set_shaping_time', { group: group, value: parseInt(input.value) });
}

function setGain(deviceId, group) {
    const input = group === 5
        ? document.getElementById(`gain-common-${deviceId}`)
        : document.getElementById(`gain-${deviceId}-${group}`);
    sendCommand(deviceId, 'set_gain', { group: group, value: parseInt(input.value) });
}

function setCoincidenceWindow(deviceId) {
    const input = document.getElementById(`coincidence-${deviceId}`);
    sendCommand(deviceId, 'set_coincidence_window', { value: parseInt(input.value) });
}

function setShaperOffset(deviceId) {
    const input = document.getElementById(`shaper-offset-${deviceId}`);
    sendCommand(deviceId, 'set_shaper_offset', { value: parseInt(input.value) });
}

function setThresholdOffset(deviceId) {
    const input = document.getElementById(`threshold-offset-${deviceId}`);
    sendCommand(deviceId, 'set_threshold_offset', { value: parseInt(input.value) });
}

function setBLRThreshold(deviceId) {
    const input = document.getElementById(`blr-threshold-${deviceId}`);
    sendCommand(deviceId, 'set_blr_threshold', { value: parseInt(input.value) });
}

function setMultiplicity(deviceId) {
    const hi = parseInt(document.getElementById(`mult-hi-${deviceId}`).value);
    const lo = parseInt(document.getElementById(`mult-lo-${deviceId}`).value);
    sendCommand(deviceId, 'set_multiplicity_borders', { hi: hi, lo: lo });
}

function setTimingFilter(deviceId, value) {
    sendCommand(deviceId, 'set_timing_filter', { value: parseInt(value) });
}

function viewSettings(deviceId) {
    alert('View Settings feature - to be implemented');
}

function loadRCSettings(deviceId) {
    alert('Load RC Settings - settings will be loaded automatically on connection');
}

function copyRCToPanel(deviceId) {
    sendCommand(deviceId, 'copy_rc_to_panel', {});
}

function copyPanelToRC(deviceId) {
    sendCommand(deviceId, 'copy_panel_to_rc', {});
}

// Update initial values
function updateInitialValues(deviceId, data) {
    const modulePanel = document.querySelector(`.device-tab[data-device-id="${deviceId}"]`);
    if (!modulePanel) return;

    switch (data.type) {
        case 'version':
            document.getElementById(`version-${deviceId}`).textContent = data.value;
            break;
        case 'threshold':
            const threshInput = document.getElementById(`thresh-${deviceId}-${data.channel}`);
            if (threshInput) threshInput.value = data.value;
            break;
        case 'threshold_common':
            const threshCommonInput = document.getElementById(`thresh-common-${deviceId}`);
            if (threshCommonInput) threshCommonInput.value = data.value;
            break;
        case 'pz':
            const pzInput = document.getElementById(`pz-${deviceId}-${data.channel}`);
            if (pzInput) pzInput.value = data.value;
            break;
        case 'pz_common':
            const pzCommonInput = document.getElementById(`pz-common-${deviceId}`);
            if (pzCommonInput) pzCommonInput.value = data.value;
            break;
        case 'shaping_time':
            const shapingInput = document.getElementById(`shaping-${deviceId}-${data.group}`);
            if (shapingInput) shapingInput.value = data.value;
            break;
        case 'shaping_time_common':
            const shapingCommonInput = document.getElementById(`shaping-common-${deviceId}`);
            if (shapingCommonInput) shapingCommonInput.value = data.value;
            break;
        case 'gain':
            const gainInput = document.getElementById(`gain-${deviceId}-${data.group}`);
            if (gainInput) gainInput.value = data.value;
            break;
        case 'gain_common':
            const gainCommonInput = document.getElementById(`gain-common-${deviceId}`);
            if (gainCommonInput) gainCommonInput.value = data.value;
            break;
        case 'monitor':
            const monitorSelect = document.getElementById(`monitor-${deviceId}`);
            if (monitorSelect) monitorSelect.value = data.value;
            break;
        case 'multiplicity':
            const multHiInput = document.getElementById(`mult-hi-${deviceId}`);
            const multLoInput = document.getElementById(`mult-lo-${deviceId}`);
            if (multHiInput) multHiInput.value = data.hi;
            if (multLoInput) multLoInput.value = data.lo;
            break;
        case 'coincidence_window':
            const coincidenceInput = document.getElementById(`coincidence-${deviceId}`);
            if (coincidenceInput) coincidenceInput.value = data.value;
            break;
        case 'threshold_offset':
            const thresholdOffsetInput = document.getElementById(`threshold-offset-${deviceId}`);
            if (thresholdOffsetInput) thresholdOffsetInput.value = data.value;
            break;
        case 'shaper_offset':
            const shaperOffsetInput = document.getElementById(`shaper-offset-${deviceId}`);
            if (shaperOffsetInput) shaperOffsetInput.value = data.value;
            break;
        case 'blr_threshold':
            const blrThresholdInput = document.getElementById(`blr-threshold-${deviceId}`);
            if (blrThresholdInput) blrThresholdInput.value = data.value;
            break;
        case 'timing_filter':
            const timingFilterSelect = document.getElementById(`timing-filter-${deviceId}`);
            if (timingFilterSelect) timingFilterSelect.value = data.value;
            break;
        case 'single_mode':
            const singleModeCheck = document.getElementById(`single-mode-${deviceId}`);
            if (singleModeCheck) singleModeCheck.checked = data.value;
            break;
        case 'ecl_delay':
            const eclDelayCheck = document.getElementById(`ecl-delay-${deviceId}`);
            if (eclDelayCheck) eclDelayCheck.checked = data.value;
            break;
        case 'blr_mode':
            const blrModeCheck = document.getElementById(`blr-mode-${deviceId}`);
            if (blrModeCheck) blrModeCheck.checked = data.value;
            break;
        case 'rc_mode':
            const rcModeCheck = document.getElementById(`rc-mode-${deviceId}`);
            if (rcModeCheck) rcModeCheck.checked = data.value;
            break;
    }
}

