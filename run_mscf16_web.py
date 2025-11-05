#!/usr/bin/env python3
"""
Run MSCF-16 Web Server

Usage:
    python run_mscf16_web.py [--host HOST] [--port PORT] [--debug]
"""

import sys
from mscf16_web_server import app, socketio

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='MSCF-16 Web Server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to (default: 0.0.0.0 for external access)')
    parser.add_argument('--port', type=int, default=5001, help='Port to bind to (default: 5001)')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    args = parser.parse_args()

    print(f"Starting MSCF-16 Web Server on http://{args.host}:{args.port}")
    print(f"Access from external: http://<your-ip>:{args.port}")
    print(f"Open your browser and navigate to the URL above")
    socketio.run(app, host=args.host, port=args.port, debug=args.debug)

