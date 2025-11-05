"""
MSCF-16 Web Server Application

Flask 기반의 MSCF-16 장치 제어 웹 애플리케이션
기존 PyQt5 GUI와 유사한 인터페이스 제공
"""

import sys
import serial.tools.list_ports
import threading
import time
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
from typing import Dict, Optional
from mscf16_controller import MSCF16Controller, MSCF16Error

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mscf16_web_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*")

# Global device management
devices: Dict[str, MSCF16Controller] = {}
update_timers: Dict[str, threading.Timer] = {}
update_intervals: Dict[str, bool] = {}


def get_available_ports():
    """Get list of available serial ports"""
    ports = serial.tools.list_ports.comports()
    return [{"device": port.device, "description": port.description} for port in ports]


@app.route('/')
def index():
    """Main page"""
    return render_template('mscf16_index.html')


@app.route('/api/ports', methods=['GET'])
def api_ports():
    """Get available serial ports"""
    return jsonify(get_available_ports())


@app.route('/api/connect', methods=['POST'])
def api_connect():
    """Connect to device"""
    data = request.json
    port = data.get('port')
    baudrate = data.get('baudrate', 9600)
    device_id = data.get('device_id', port)

    if not port:
        return jsonify({"success": False, "error": "Port not specified"}), 400

    try:
        if device_id in devices:
            return jsonify({"success": False, "error": "Device already connected"}), 400

        controller = MSCF16Controller(port=port, baudrate=baudrate)
        controller.connect()

        if controller.is_connected:
            devices[device_id] = controller
            update_intervals[device_id] = True
            start_update_timer(device_id)

            # Load initial values
            load_initial_values(device_id)

            return jsonify({
                "success": True,
                "device_id": device_id,
                "message": f"Connected to {port}"
            })
        else:
            return jsonify({"success": False, "error": "Connection failed"}), 500

    except MSCF16Error as e:
        return jsonify({"success": False, "error": str(e)}), 500
    except Exception as e:
        return jsonify({"success": False, "error": f"Unexpected error: {str(e)}"}), 500


@app.route('/api/disconnect/<device_id>', methods=['POST'])
def api_disconnect(device_id):
    """Disconnect from device"""
    try:
        if device_id in devices:
            stop_update_timer(device_id)
            controller = devices[device_id]
            controller.disconnect()
            del devices[device_id]
            if device_id in update_intervals:
                del update_intervals[device_id]

            socketio.emit('device_disconnected', {'device_id': device_id})
            return jsonify({"success": True, "message": "Disconnected"})
        else:
            return jsonify({"success": False, "error": "Device not found"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/command/<device_id>', methods=['POST'])
def api_command(device_id):
    """Send command to device"""
    data = request.json
    command = data.get('command')
    params = data.get('params', {})

    if device_id not in devices:
        return jsonify({"success": False, "error": "Device not connected"}), 404

    controller = devices[device_id]

    try:
        if command == 'set_threshold':
            channel = params.get('channel')
            value = params.get('value')
            result = controller.set_threshold(channel, value)
            return jsonify({"success": True, "result": result})
        elif command == 'set_pz_value':
            channel = params.get('channel')
            value = params.get('value')
            result = controller.set_pz_value(channel, value)
            return jsonify({"success": True, "result": result})
        elif command == 'set_monitor_channel':
            channel = params.get('channel')
            result = controller.set_monitor_channel(channel)
            return jsonify({"success": True, "result": result})
        elif command == 'set_automatic_pz':
            channel = params.get('channel')  # None for toggle
            if channel is not None:
                result = controller.set_automatic_pz(channel)
            else:
                result = controller.toggle_automatic_pz()
            return jsonify({"success": True, "result": result})
        elif command == 'set_shaping_time':
            group = params.get('group')
            value = params.get('value')
            result = controller.set_shaping_time(group, value)
            return jsonify({"success": True, "result": result})
        elif command == 'set_gain':
            group = params.get('group')
            value = params.get('value')
            result = controller.set_gain(group, value)
            return jsonify({"success": True, "result": result})
        elif command == 'set_coincidence_window':
            value = params.get('value')
            result = controller.set_coincidence_window(value)
            return jsonify({"success": True, "result": result})
        elif command == 'set_threshold_offset':
            value = params.get('value')
            result = controller.set_threshold_offset(value)
            return jsonify({"success": True, "result": result})
        elif command == 'set_shaper_offset':
            value = params.get('value')
            result = controller.set_shaper_offset(value)
            return jsonify({"success": True, "result": result})
        elif command == 'set_blr_threshold':
            value = params.get('value')
            result = controller.set_blr_threshold(value)
            return jsonify({"success": True, "result": result})
        elif command == 'set_multiplicity_borders':
            hi = params.get('hi')
            lo = params.get('lo')
            result = controller.set_multiplicity_borders(hi, lo)
            return jsonify({"success": True, "result": result})
        elif command == 'set_timing_filter':
            value = params.get('value')
            result = controller.set_timing_filter(value)
            return jsonify({"success": True, "result": result})
        elif command == 'set_single_channel_mode':
            enable = params.get('enable')
            result = controller.set_single_channel_mode(enable)
            return jsonify({"success": True, "result": result})
        elif command == 'set_ecl_delay':
            enable = params.get('enable')
            result = controller.set_ecl_delay(enable)
            return jsonify({"success": True, "result": result})
        elif command == 'set_blr_mode':
            enable = params.get('enable')
            result = controller.set_blr_mode(enable)
            return jsonify({"success": True, "result": result})
        elif command == 'switch_rc_mode_on':
            result = controller.switch_rc_mode_on()
            return jsonify({"success": True, "result": result})
        elif command == 'switch_rc_mode_off':
            result = controller.switch_rc_mode_off()
            return jsonify({"success": True, "result": result})
        elif command == 'get_version':
            result = controller.get_version()
            return jsonify({"success": True, "result": result})
        elif command == 'copy_rc_to_panel':
            result = controller.copy_rc_to_panel()
            return jsonify({"success": True, "result": result})
        elif command == 'copy_panel_to_rc':
            result = controller.copy_panel_to_rc()
            return jsonify({"success": True, "result": result})
        else:
            return jsonify({"success": False, "error": f"Unknown command: {command}"}), 400

    except MSCF16Error as e:
        return jsonify({"success": False, "error": str(e)}), 500
    except Exception as e:
        return jsonify({"success": False, "error": f"Unexpected error: {str(e)}"}), 500


def load_initial_values(device_id):
    """Load initial values from device"""
    if device_id not in devices:
        return

    controller = devices[device_id]

    try:
        # Parse display_setup
        panel_set, rc_set, gen_set = controller.display_setup_parsed()

        # Load version
        try:
            version = controller.get_version()
            socketio.emit('initial_values', {
                'device_id': device_id,
                'type': 'version',
                'value': version
            })
        except:
            pass

        # Load panel settings
        if 'threshs' in panel_set:
            threshs = panel_set['threshs']
            for i, value in enumerate(threshs[:16], 1):
                socketio.emit('initial_values', {
                    'device_id': device_id,
                    'type': 'threshold',
                    'channel': i,
                    'value': value
                })
            if len(threshs) > 16:
                socketio.emit('initial_values', {
                    'device_id': device_id,
                    'type': 'threshold_common',
                    'value': threshs[-1]
                })

        if 'pz' in panel_set:
            pz_values = panel_set['pz']
            for i, value in enumerate(pz_values[:16], 1):
                socketio.emit('initial_values', {
                    'device_id': device_id,
                    'type': 'pz',
                    'channel': i,
                    'value': value
                })
            if len(pz_values) > 16:
                socketio.emit('initial_values', {
                    'device_id': device_id,
                    'type': 'pz_common',
                    'value': pz_values[-1]
                })

        if 'shts' in panel_set:
            shts = panel_set['shts']
            for i, value in enumerate(shts[:4], 1):
                socketio.emit('initial_values', {
                    'device_id': device_id,
                    'type': 'shaping_time',
                    'group': i,
                    'value': value
                })
            if len(shts) > 4:
                socketio.emit('initial_values', {
                    'device_id': device_id,
                    'type': 'shaping_time_common',
                    'value': shts[-1]
                })

        if 'gains' in panel_set:
            gains = panel_set['gains']
            for i, value in enumerate(gains[:4], 1):
                socketio.emit('initial_values', {
                    'device_id': device_id,
                    'type': 'gain',
                    'group': i,
                    'value': value
                })
            if len(gains) > 4:
                socketio.emit('initial_values', {
                    'device_id': device_id,
                    'type': 'gain_common',
                    'value': gains[-1]
                })

        # Load RC settings
        if 'threshs' in rc_set:
            threshs = rc_set['threshs']
            for i, value in enumerate(threshs[:16], 1):
                socketio.emit('initial_values', {
                    'device_id': device_id,
                    'type': 'rc_threshold',
                    'channel': i,
                    'value': value
                })
            if len(threshs) > 16:
                socketio.emit('initial_values', {
                    'device_id': device_id,
                    'type': 'rc_threshold_common',
                    'value': threshs[-1]
                })

        if 'pz' in rc_set:
            pz_values = rc_set['pz']
            for i, value in enumerate(pz_values[:16], 1):
                socketio.emit('initial_values', {
                    'device_id': device_id,
                    'type': 'rc_pz',
                    'channel': i,
                    'value': value
                })
            if len(pz_values) > 16:
                socketio.emit('initial_values', {
                    'device_id': device_id,
                    'type': 'rc_pz_common',
                    'value': pz_values[-1]
                })

        if 'shts' in rc_set:
            shts = rc_set['shts']
            for i, value in enumerate(shts[:4], 1):
                socketio.emit('initial_values', {
                    'device_id': device_id,
                    'type': 'rc_shaping_time',
                    'group': i,
                    'value': value
                })
            if len(shts) > 4:
                socketio.emit('initial_values', {
                    'device_id': device_id,
                    'type': 'rc_shaping_time_common',
                    'value': shts[-1]
                })

        if 'gains' in rc_set:
            gains = rc_set['gains']
            for i, value in enumerate(gains[:4], 1):
                socketio.emit('initial_values', {
                    'device_id': device_id,
                    'type': 'rc_gain',
                    'group': i,
                    'value': value
                })
            if len(gains) > 4:
                socketio.emit('initial_values', {
                    'device_id': device_id,
                    'type': 'rc_gain_common',
                    'value': gains[-1]
                })

        if 'monitor' in rc_set:
            socketio.emit('initial_values', {
                'device_id': device_id,
                'type': 'monitor',
                'value': rc_set['monitor']
            })

        if 'mult' in rc_set:
            mult = rc_set['mult']
            socketio.emit('initial_values', {
                'device_id': device_id,
                'type': 'multiplicity',
                'hi': mult.get('high'),
                'lo': mult.get('low')
            })

        # Load general settings
        if 'coincidence_time' in gen_set:
            socketio.emit('initial_values', {
                'device_id': device_id,
                'type': 'coincidence_window',
                'value': gen_set['coincidence_time']
            })

        if 'threshold_offset' in gen_set:
            socketio.emit('initial_values', {
                'device_id': device_id,
                'type': 'threshold_offset',
                'value': gen_set['threshold_offset']
            })

        if 'shaper_offset' in gen_set:
            socketio.emit('initial_values', {
                'device_id': device_id,
                'type': 'shaper_offset',
                'value': gen_set['shaper_offset']
            })

        if 'blr_thresh' in gen_set:
            socketio.emit('initial_values', {
                'device_id': device_id,
                'type': 'blr_threshold',
                'value': gen_set['blr_thresh']
            })

        if 'tf_int' in rc_set:
            socketio.emit('initial_values', {
                'device_id': device_id,
                'type': 'timing_filter',
                'value': rc_set['tf_int']
            })

        # Load mode settings
        if 'single_mode' in rc_set:
            socketio.emit('initial_values', {
                'device_id': device_id,
                'type': 'single_mode',
                'value': rc_set['single_mode']
            })

        if 'ecl_delay' in rc_set:
            socketio.emit('initial_values', {
                'device_id': device_id,
                'type': 'ecl_delay',
                'value': rc_set['ecl_delay']
            })

        if 'blr_active' in rc_set:
            socketio.emit('initial_values', {
                'device_id': device_id,
                'type': 'blr_mode',
                'value': rc_set['blr_active']
            })

        if 'rc_mode' in rc_set:
            socketio.emit('initial_values', {
                'device_id': device_id,
                'type': 'rc_mode',
                'value': rc_set['rc_mode']
            })

    except Exception as e:
        print(f"Error loading initial values: {e}")


def start_update_timer(device_id):
    """Start update timer for device"""
    if device_id in update_timers:
        update_timers[device_id].cancel()

    if update_intervals.get(device_id, False):
        timer = threading.Timer(1.0, lambda: None)  # No periodic updates needed for MSCF16
        timer.daemon = True
        timer.start()
        update_timers[device_id] = timer


def stop_update_timer(device_id):
    """Stop update timer for device"""
    if device_id in update_timers:
        update_timers[device_id].cancel()
        del update_timers[device_id]
    update_intervals[device_id] = False


@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    emit('connected', {'message': 'Connected to server'})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    pass


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='MSCF-16 Web Server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to (default: 0.0.0.0 for external access)')
    parser.add_argument('--port', type=int, default=5001, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    args = parser.parse_args()

    print(f"Starting MSCF-16 Web Server on http://{args.host}:{args.port}")
    print(f"Access from external: http://<your-ip>:{args.port}")
    socketio.run(app, host=args.host, port=args.port, debug=args.debug)

