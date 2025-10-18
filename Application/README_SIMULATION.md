# 🏥 Hospital Simulation Dashboard

A dynamic web application that visualizes a hospital simulation with real-time dashboards showing patient flow, wait times, provider utilization, and queue management.

## Features

### Real-Time Visualization
- 📊 **Live Statistics**: Total patients, critical vs normal status, bed occupancy
- ⏱ **Wait Time Tracking**: Real-time average wait times with trending charts
- 📋 **Queue Management**: Visual status of all priority queues (first visit, SLA, critical, normal)
- 👨‍⚕️ **Provider Utilization**: Doctor and nurse workload monitoring
- 🔄 **Patient Flow**: Arrivals vs discharges with hourly breakdowns

### Interactive Controls
- ▶️ **Start Simulation**: Begin the hospital simulation
- ⏹ **Stop Simulation**: Pause the simulation at any time
- 🔄 **Reset**: Clear all data and restart from beginning

### Event Tracking
- 📢 **Real-time Events Log**: Live feed of all simulation events
- 🚑 **Patient Arrivals**: New patient admissions with status
- 🏥 **Dispatching**: Provider assignments and wait times
- 💊 **Service Events**: Treatment start/completion
- 🚪 **Discharges**: Patient releases with summary statistics

## Quick Start

### 1. Install Dependencies
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install required packages
pip install flask flask-socketio simpy
```

### 2. Run the Application
```bash
# Option 1: Direct execution
source venv/bin/activate
python hospital_app.py

# Option 2: Using the runner script
python run_simulation.py
```

### 3. Access the Dashboard
Open your web browser and navigate to:
```
http://localhost:5001
```

## Simulation Details

### Hospital Configuration
- **Bed Capacity**: 20 beds
- **Initial Patients**: 20 patients already admitted
- **Providers**: 2 doctors + 5 nurses
- **Simulation Duration**: 7 days (accelerated for demo)

### Priority Queue System
1. **First Visit Queue** (Highest Priority): Patients never seen before
2. **Daily SLA Queue**: Patients who must be seen today
3. **Critical Queue**: Critical status patients
4. **Normal Fast Queue**: Normal patients fast-tracked due to SLA breach
5. **Normal Queue**: Regular normal status patients

### Patient Flow
- **Arrivals**: 1 patient every 12 hours
- **Status Distribution**: 80% normal, 20% critical
- **Status Changes**: Daily probability of status transitions
- **Length of Stay**: 3-5 days (normal), 5-8 days (critical)

### Provider Capacity
- **Doctors**: 40 patients per day capacity
- **Nurses**: 25-40 patients per day (varies)
- **Service Times**: 
  - Critical: 15-45 minutes
  - Normal: 10-25 minutes
  - Nurse care: 10-20 minutes

## Technical Architecture

### Backend Components
- **Flask + SocketIO**: Real-time web application framework
- **SimPy**: Discrete event simulation engine
- **Threading**: Concurrent simulation execution

### Frontend Components
- **Chart.js**: Interactive charts and graphs
- **Socket.IO Client**: Real-time communication
- **Responsive CSS**: Mobile-friendly dashboard design

### Files Structure
```
├── hospital_app.py          # Main Flask application
├── simulation.py            # Modified simulation with real-time events
├── run_simulation.py        # Startup script
├── templates/
│   └── dashboard.html       # Main dashboard interface
├── static/
│   └── dashboard.js         # Frontend JavaScript logic
└── venv/                    # Python virtual environment
```

## Dashboard Sections

### Key Statistics Panel
- Total active patients
- Critical vs normal patient counts
- Average current wait time
- Bed occupancy percentage
- Provider utilization rate

### Queue Status Panel
Visual representation of all priority queues with real-time counts.

### Charts and Trends
- **Wait Time Trends**: Line chart showing average wait times over time
- **Patient Flow**: Bar chart comparing arrivals vs discharges
- **Provider Utilization**: Doughnut chart showing busy vs available providers

### Real-time Events Log
Chronological feed of all simulation events with color-coded event types:
- 🟢 Patient arrivals
- 🔵 Provider dispatching
- 🟣 Service events
- 🔴 Patient discharges
- 🟡 Status changes

## Performance Notes

- Simulation runs at 1000x speed for demonstration purposes
- Charts update every minute for performance
- Event log keeps last 50 events to prevent memory issues
- Charts maintain last 20 data points for readability

## Customization

### Modify Simulation Parameters
Edit values in `simulation.py`:
- `SIM_DAYS`: Simulation duration
- `BED_CAPACITY`: Hospital bed count
- `NUM_DOCTORS`, `NUM_NURSES`: Provider staffing
- `ARRIVAL_RATE_PER_DAY`: Patient arrival frequency

### Adjust Visualization
Modify chart configurations in `static/dashboard.js`:
- Chart types and styling
- Update frequencies
- Data retention limits

## Troubleshooting

### Common Issues

**Port Already in Use**
```bash
# Change port in hospital_app.py or kill existing process
lsof -ti:5001 | xargs kill -9
```

**Missing Dependencies**
```bash
# Ensure virtual environment is activated
source venv/bin/activate
pip install -r requirements.txt  # if available
```

**Connection Issues**
- Check that the server is running on port 5001
- Verify firewall settings allow local connections
- Try accessing via 127.0.0.1:5001 instead of localhost

### Browser Compatibility
- Modern browsers with WebSocket support required
- Tested on Chrome, Firefox, Safari, Edge
- Mobile responsive design works on tablets and phones

## Future Enhancements

Potential improvements for the simulation dashboard:
- Historical data persistence with database
- Advanced analytics and reporting
- Multiple hospital scenarios
- Resource optimization suggestions
- Patient journey visualization
- Export capabilities for data analysis

---

**Created for Six Sigma Hackathon** 📈  
Real-time hospital simulation visualization system