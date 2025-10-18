#!/usr/bin/env python3
"""
Hospital Simulation Web Application Runner
"""

import os
import sys

def main():
    # Activate virtual environment if available
    venv_path = os.path.join(os.path.dirname(__file__), 'venv', 'bin', 'activate_this.py')
    if os.path.exists(venv_path):
        exec(open(venv_path).read(), {'__file__': venv_path})
    
    # Import and run the hospital app
    from hospital_app import app, socketio
    
    print("🏥 Starting Hospital Simulation Dashboard...")
    print("📊 Dashboard will be available at: http://localhost:5001")
    print("🔄 Use Ctrl+C to stop the server")
    print("-" * 50)
    
    try:
        socketio.run(app, debug=True, host='0.0.0.0', port=5001)
    except KeyboardInterrupt:
        print("\n👋 Simulation server stopped.")

if __name__ == '__main__':
    main()