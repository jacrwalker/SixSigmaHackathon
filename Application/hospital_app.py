from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import threading
import json
import time
from simulation import HospitalSimulation
from simulation2_wrapper import Simulation2Wrapper

app = Flask(__name__)
app.config['SECRET_KEY'] = 'hospital_sim_secret'
socketio = SocketIO(app, cors_allowed_origins="*")

simulation = None
simulation_thread = None
simulation_running = False

# Simulation2 globals
simulation2 = None
simulation2_thread = None
simulation2_running = False

# Shared configuration for both simulations
simulation_config = {
    'hospital_beds': 20,
    'initial_patients': 18,
    'simulation_weeks': 4,
    'num_doctors': 3,
    'num_nurses': 5,
    'nurses_max_patients': 4,
    'patient_influx_per_12h': 1,
    'simulation_speed': 100
}

@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/simulation2')
def simulation2_dashboard():
    return render_template('simulation2_dashboard.html')

@socketio.on('connect')
def handle_connect():
    print('Client connected')
    emit('status', {'message': 'Connected to hospital simulation'})

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('start_simulation')
def handle_start_simulation():
    global simulation, simulation_thread, simulation_running
    
    if simulation_running:
        emit('status', {'message': 'Simulation already running'})
        return
    
    simulation_running = True
    simulation = HospitalSimulation(socketio, simulation_config)
    simulation_thread = threading.Thread(target=run_simulation)
    simulation_thread.daemon = True
    simulation_thread.start()
    
    emit('status', {'message': 'Simulation started'})

@socketio.on('stop_simulation')
def handle_stop_simulation():
    global simulation_running
    simulation_running = False
    if simulation:
        simulation.stop()
    emit('status', {'message': 'Simulation stopped'})

@socketio.on('reset_simulation')
def handle_reset_simulation():
    global simulation, simulation_running
    simulation_running = False
    if simulation:
        simulation.stop()
    
    socketio.emit('reset_dashboard')
    emit('status', {'message': 'Simulation reset'})

@socketio.on('get_patient_details')
def handle_get_patient_details(data):
    global simulation
    if simulation and simulation_running:
        patient_id = data.get('patient_id')
        # Find patient by ID
        for patient in simulation.patients:
            if patient.pid == patient_id:
                patient_data = simulation.get_patient_data(patient)
                emit('patient_details', patient_data)
                return
        emit('patient_details', {'error': 'Patient not found'})
    else:
        emit('patient_details', {'error': 'Simulation not running'})

# Simulation2 SocketIO handlers
@socketio.on('start_simulation2')
def handle_start_simulation2():
    global simulation2, simulation2_thread, simulation2_running
    
    if simulation2_running:
        emit('status2', {'message': 'Simulation2 already running'})
        return
    
    simulation2_running = True
    simulation2 = Simulation2Wrapper(socketio, simulation_config)
    simulation2_thread = threading.Thread(target=run_simulation2)
    simulation2_thread.daemon = True
    simulation2_thread.start()
    
    emit('status2', {'message': 'Simulation2 started'})

@socketio.on('stop_simulation2')
def handle_stop_simulation2():
    global simulation2_running
    simulation2_running = False
    if simulation2:
        simulation2.stop()
    emit('status2', {'message': 'Simulation2 stopped'})

@socketio.on('reset_simulation2')
def handle_reset_simulation2():
    global simulation2, simulation2_running
    simulation2_running = False
    if simulation2:
        simulation2.stop()
    
    socketio.emit('reset_dashboard2')
    emit('status2', {'message': 'Simulation2 reset'})

# Configuration management handlers
@socketio.on('get_config')
def handle_get_config():
    emit('config_data', simulation_config)

@socketio.on('update_config')
def handle_update_config(data):
    global simulation_config
    
    # Validate and update configuration
    try:
        simulation_config['hospital_beds'] = max(1, int(data.get('hospital_beds', 20)))
        simulation_config['initial_patients'] = max(0, min(int(data.get('initial_patients', 18)), simulation_config['hospital_beds']))
        simulation_config['simulation_weeks'] = max(1, int(data.get('simulation_weeks', 4)))
        simulation_config['num_doctors'] = max(1, int(data.get('num_doctors', 3)))
        simulation_config['num_nurses'] = max(1, int(data.get('num_nurses', 5)))
        simulation_config['nurses_max_patients'] = max(1, int(data.get('nurses_max_patients', 4)))
        simulation_config['patient_influx_per_12h'] = max(0, int(data.get('patient_influx_per_12h', 1)))
        simulation_config['simulation_speed'] = max(1, min(int(data.get('simulation_speed', 100)), 1000))
        
        emit('config_updated', {'success': True, 'config': simulation_config})
        # Broadcast to all clients
        socketio.emit('config_data', simulation_config)
    except (ValueError, TypeError) as e:
        emit('config_updated', {'success': False, 'error': str(e)})

def run_simulation():
    global simulation_running
    try:
        simulation.run()
    except Exception as e:
        print(f"Simulation error: {e}")
    finally:
        simulation_running = False
        socketio.emit('simulation_complete')

def run_simulation2():
    global simulation2_running
    try:
        simulation2.run()
    except Exception as e:
        print(f"Simulation2 error: {e}")
    finally:
        simulation2_running = False
        socketio.emit('simulation2_complete')

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5002, allow_unsafe_werkzeug=True)