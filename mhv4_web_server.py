"""
MHV-4 Web Server Application

Flask 기반의 MHV-4 장치 제어 웹 애플리케이션
기존 PyQt5 GUI와 유사한 인터페이스 제공
"""

import sys
import serial.tools.list_ports
import threading
import time
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
from typing import Dict, Optional
from mhv4_controller import MHV4Controller, MHV4Error

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mhv4_web_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*")

# Global device management
devices: Dict[str, MHV4Controller] = {}
update_timers: Dict[str, threading.Timer] = {}
update_intervals: Dict[str, bool] = {}


def get_available_ports():
    """Get list of available serial ports"""
    ports = serial.tools.list_ports.comports()
    return [{"device": port.device, "description": port.description} for port in ports]


@app.route('/')
def index():
    """Main page"""
    return render_template('mhv4_index.html')


@app.route('/api/ports', methods=['GET'])
def api_ports():
    """Get available serial ports"""
    return jsonify(get_available_ports())


@app.route('/api/connect', methods=['POST'])
def api_connect():
    """Connect to device"""
    data = request.json
    port = data.get('port')
    device_id = data.get('device_id', port)  # Use port as device_id if not provided

    if not port:
        return jsonify({"success": False, "error": "Port not specified"}), 400

    try:
        if device_id in devices:
            return jsonify({"success": False, "error": "Device already connected"}), 400

        controller = MHV4Controller(port=port, baudrate=9600)
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

    except MHV4Error as e:
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
        if command == 'turn_on':
            channel = params.get('channel')
            result = controller.turn_on(channel)
            return jsonify({"success": True, "result": result})
        elif command == 'turn_off':
            channel = params.get('channel')
            result = controller.turn_off(channel)
            return jsonify({"success": True, "result": result})
        elif command == 'set_voltage':
            channel = params.get('channel')
            voltage_01v = int(params.get('voltage') * 10)
            result = controller.set_voltage(channel, voltage_01v)
            return jsonify({"success": True, "result": result})
        elif command == 'set_voltage_limit':
            channel = params.get('channel')
            voltage_limit_01v = int(params.get('voltage_limit') * 10)
            result = controller.set_voltage_limit(channel, voltage_limit_01v)
            return jsonify({"success": True, "result": result})
        elif command == 'set_current_limit':
            channel = params.get('channel')
            current_limit_na = int(params.get('current_limit') * 1000)
            result = controller.set_current_limit(channel, current_limit_na)
            return jsonify({"success": True, "result": result})
        elif command == 'set_polarity':
            channel = params.get('channel')
            polarity = params.get('polarity')  # 'p' or 'n'
            result = controller.set_polarity(channel, polarity)
            return jsonify({"success": True, "result": result})
        elif command == 'set_auto_shutdown':
            channel = params.get('channel')
            enable = params.get('enable')
            result = controller.set_auto_shutdown(channel, enable)
            return jsonify({"success": True, "result": result})
        elif command == 'set_temperature_compensation':
            channel = params.get('channel')
            ntc_channel = params.get('ntc_channel')  # 0-3 or None
            result = controller.set_temperature_compensation(channel, ntc_channel)
            return jsonify({"success": True, "result": result})
        elif command == 'set_reference_temperature':
            channel = params.get('channel')
            temp_01c = int(params.get('temperature') * 10)
            result = controller.set_reference_temperature(channel, temp_01c)
            return jsonify({"success": True, "result": result})
        elif command == 'set_temperature_slope':
            channel = params.get('channel')
            slope = params.get('slope')
            result = controller.set_temperature_slope(channel, slope)
            return jsonify({"success": True, "result": result})
        elif command == 'set_ramp_speed':
            ramp_speed_index = params.get('ramp_speed_index')
            result = controller.set_ramp_speed(ramp_speed_index)
            return jsonify({"success": True, "result": result})
        else:
            return jsonify({"success": False, "error": f"Unknown command: {command}"}), 400

    except MHV4Error as e:
        return jsonify({"success": False, "error": str(e)}), 500
    except Exception as e:
        return jsonify({"success": False, "error": f"Unexpected error: {str(e)}"}), 500


def load_initial_values(device_id):
    """Load initial values from device"""
    if device_id not in devices:
        return

    controller = devices[device_id]

    try:
        # Load ramp speed
        try:
            response = controller.read_ramp_speed()
            if response:
                ramp_speed = int(response.split()[-2])
                ramp_speed_dict = {5: 0, 25: 1, 100: 2, 500: 3}
                if ramp_speed in ramp_speed_dict:
                    socketio.emit('initial_values', {
                        'device_id': device_id,
                        'type': 'ramp_speed',
                        'value': ramp_speed_dict[ramp_speed]
                    })
        except:
            pass

        # Load values for each channel
        for ch in range(4):
            # Load voltage preset
            try:
                response = controller.read_voltage_preset(ch)
                value = parse_value(response)
                if value is not None:
                    socketio.emit('initial_values', {
                        'device_id': device_id,
                        'channel': ch,
                        'type': 'voltage_preset',
                        'value': abs(value)
                    })
            except:
                pass

            # Load voltage limit
            try:
                response = controller.read_voltage_limit(ch)
                value = parse_value(response)
                if value is not None:
                    socketio.emit('initial_values', {
                        'device_id': device_id,
                        'channel': ch,
                        'type': 'voltage_limit',
                        'value': abs(value)
                    })
            except:
                pass

            # Load current limit
            try:
                response = controller.read_current_limit(ch)
                value = parse_value(response)
                if value is not None:
                    socketio.emit('initial_values', {
                        'device_id': device_id,
                        'channel': ch,
                        'type': 'current_limit',
                        'value': abs(value) / 1000.0  # Convert nA to μA
                    })
            except:
                pass

            # Load polarity
            try:
                response = controller.read_polarity(ch)
                polarity = response.split()[-1].strip().lower()
                socketio.emit('initial_values', {
                    'device_id': device_id,
                    'channel': ch,
                    'type': 'polarity',
                    'value': 'p' if polarity == 'positive' else 'n'
                })
            except:
                pass

            # Load temperature compensation
            try:
                response = controller.read_temperature_compensation(ch)
                parts = response.split()
                parts[4] = parts[4][:-1]
                if parts[4].lower() in ['off', '-', '4']:
                    ntc_index = 0
                else:
                    ntc_index = int(parts[4]) + 1
                socketio.emit('initial_values', {
                    'device_id': device_id,
                    'channel': ch,
                    'type': 'ntc',
                    'value': ntc_index
                })

                # Load reference temperature
                try:
                    ref_temp = float(parts[6])
                    socketio.emit('initial_values', {
                        'device_id': device_id,
                        'channel': ch,
                        'type': 'ref_temp',
                        'value': ref_temp
                    })
                except:
                    pass

                # Load temperature slope
                try:
                    slope = int(parts[9])
                    socketio.emit('initial_values', {
                        'device_id': device_id,
                        'channel': ch,
                        'type': 'slope',
                        'value': slope
                    })
                except:
                    pass
            except:
                pass

    except Exception as e:
        print(f"Error loading initial values: {e}")


def parse_value(response: str) -> Optional[float]:
    """Parse numeric value from response string"""
    if not response or not response.strip():
        return None

    try:
        parts = response.strip().split()
        for part in reversed(parts):
            cleaned = part.strip()
            try:
                value = float(cleaned)
                return value
            except ValueError:
                continue
    except Exception:
        pass
    return None


def update_readings(device_id):
    """Update readings for a device"""
    if device_id not in devices or not update_intervals.get(device_id, False):
        return

    controller = devices[device_id]

    if not controller.is_connected:
        return

    try:
        readings = {}
        for ch in range(4):
            # Read voltage
            try:
                voltage_response = controller.read_voltage(ch)
                voltage = parse_voltage(voltage_response)
                readings[f'voltage_{ch}'] = voltage
            except:
                pass

            # Read current
            try:
                current_response = controller.read_current(ch)
                current = parse_current(current_response)
                readings[f'current_{ch}'] = current
            except:
                pass

            # Read power status (would need read command if available)
            # For now, assume it's based on voltage

        socketio.emit('readings_update', {
            'device_id': device_id,
            'readings': readings
        })
    except Exception as e:
        print(f"Error updating readings: {e}")

    # Schedule next update
    start_update_timer(device_id)


def parse_voltage(response: str) -> Optional[float]:
    """Parse voltage from response"""
    if not response:
        return None
    try:
        parts = response.strip().split()
        for part in reversed(parts):
            try:
                value = float(part)
                if value > 8000:
                    return value / 10.0
                elif value > 800:
                    return value / 10.0
                elif -800 <= value <= 800:
                    return abs(value)
            except ValueError:
                continue
    except:
        pass
    return None


def parse_current(response: str) -> Optional[float]:
    """Parse current from response (returns in μA)"""
    if not response:
        return None
    try:
        parts = response.strip().split()
        for part in reversed(parts):
            try:
                value = float(part)
                if value > 1000:
                    return value / 1000.0
                elif value > 100:
                    return value / 1000.0
                return value
            except ValueError:
                continue
    except:
        pass
    return None


def start_update_timer(device_id):
    """Start update timer for device"""
    if device_id in update_timers:
        update_timers[device_id].cancel()

    if update_intervals.get(device_id, False):
        timer = threading.Timer(1.0, update_readings, args=[device_id])
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
    parser = argparse.ArgumentParser(description='MHV-4 Web Server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to (default: 0.0.0.0 for external access)')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    args = parser.parse_args()

    print(f"Starting MHV-4 Web Server on http://{args.host}:{args.port}")
    print(f"Access from external: http://<your-ip>:{args.port}")
    socketio.run(app, host=args.host, port=args.port, debug=args.debug)
