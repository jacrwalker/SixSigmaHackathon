# Hospital Simulation Dashboard - Setup Guide

This guide will help you set up and run the Hospital Simulation Dashboard from scratch after downloading it from GitHub.

## 📋 Prerequisites

Before you begin, make sure you have the following installed on your system:

- **Python 3.8 or higher** ([Download Python](https://www.python.org/downloads/))
- **Git** ([Download Git](https://git-scm.com/downloads))
- **A modern web browser** (Chrome, Firefox, Safari, or Edge)

## 🚀 Quick Start

### Step 1: Download the Project

```bash
# Clone the repository from GitHub
git clone <repository-url>

# Navigate to the project directory
cd SixSigmaHackathon
```

### Step 2: Create a Virtual Environment

```bash
# Create a virtual environment (recommended)
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
# Install required Python packages using requirements.txt
pip install -r requirements.txt
```

### Step 4: Run the Application

```bash
# Start the hospital simulation dashboard
python hospital_app.py
```

You should see output similar to:
```
 * Serving Flask app 'hospital_app'
 * Debug mode: on
 * Running on http://127.0.0.1:5002
```

### Step 5: Access the Dashboard

Open your web browser and go to:

- **Simulation 1 (Critical/Normal)**: http://localhost:5002/
- **Simulation 2 (Severity Scale 1-100)**: http://localhost:5002/simulation2

## 🎛️ Using the Dashboard

### Controls Available:
- **▶ Start Simulation**: Begin the hospital simulation
- **⏹ Stop Simulation**: Pause the running simulation
- **🔄 Reset**: Reset all data and charts
- **⚙️ Settings**: Configure simulation parameters

### Available Simulations:

#### Simulation 1 (Critical/Normal System)
- Uses a binary patient classification (Critical vs Normal)
- Features queue management and SLA tracking
- Shows patient flow through different priority queues

#### Simulation 2 (Severity Scale System)
- Uses a 1-100 severity scale for patients
- Shows real-time severity changes based on waiting and treatment
- Displays severity distribution and trends

### Settings Configuration:

Click the **⚙️ Settings** button to configure:

**🏥 Hospital Configuration:**
- Hospital Beds (1-100)
- Initial Patients (0-100)

**👩‍⚕️ Staff Configuration:**
- Number of Doctors (1-20)
- Number of Nurses (1-20)
- Max Patients per Nurse (1-10)

**⏱️ Simulation Parameters:**
- Simulation Weeks (1-12)
- Patient Influx per 12 hours (0-10)
- Simulation Speed (1-1000x)

## 📁 Project Structure

```
SixSigmaHackathon/
├── hospital_app.py              # Main Flask application
├── simulation.py                # Simulation 1 logic (Critical/Normal)
├── simulation2_wrapper.py       # Simulation 2 logic (Severity scale)
├── Simulation2/                 # Original Simulation 2 files
│   ├── simulation.py
│   ├── patient.py
│   ├── staff.py
│   ├── config.py
│   └── main.py
├── templates/                   # HTML templates
│   ├── dashboard.html          # Simulation 1 dashboard
│   └── simulation2_dashboard.html # Simulation 2 dashboard
├── static/                     # JavaScript and CSS files
│   ├── dashboard.js           # Simulation 1 frontend logic
│   └── simulation2_dashboard.js # Simulation 2 frontend logic
├── oldsmulation.py            # Original simulation reference
└── readmerunapp.md           # This file
```

## 🔧 Troubleshooting

### Common Issues:

**1. Port Already in Use**
If port 5002 is already in use, you'll see an error. Either:
- Stop the process using port 5002
- Or modify `hospital_app.py` and change the port number in the last line

**2. Module Not Found Errors**
Make sure you've activated the virtual environment and installed all dependencies:
```bash
source venv/bin/activate  # On macOS/Linux
pip install -r requirements.txt
```

**3. Python Version Issues**
Ensure you're using Python 3.8 or higher:
```bash
python --version
```

**4. Virtual Environment Issues**
If virtual environment commands don't work, try:
```bash
python3 -m venv venv
```

### Performance Notes:

- **Simulation Speed**: You can adjust the simulation speed in settings (1x = real-time, 1000x = very fast)
- **Browser Performance**: For very long simulations, consider refreshing the page periodically
- **Multiple Tabs**: You can open both simulations in different browser tabs

## 🎯 Features Overview

### Real-time Visualizations:
- **Live Charts**: Patient flow, wait times, severity distributions
- **Patient Tracking**: Individual patient status and location
- **Staff Utilization**: Real-time staff assignment and availability
- **Queue Management**: Visual representation of patient queues

### Simulation Scenarios:
- **Hospital Capacity Planning**: Test different bed counts
- **Staffing Optimization**: Experiment with doctor/nurse ratios
- **Patient Flow Analysis**: Analyze wait times and treatment efficiency
- **Emergency Scenarios**: Simulate high patient influx periods

## 📊 Understanding the Results

### Key Metrics to Watch:
- **Average Wait Time**: How long patients wait for treatment
- **Bed Occupancy**: Percentage of beds in use
- **Staff Utilization**: How busy doctors and nurses are
- **Patient Severity Changes**: How patient conditions evolve over time
- **Discharge Rates**: How quickly patients complete treatment

### Comparing Simulations:
- Run the same scenario on both simulation types
- Compare average wait times and patient outcomes
- Analyze how different queue systems affect patient flow

## 🤝 Support

If you encounter any issues:

1. **Check the Console**: Look for error messages in the terminal where you ran `python hospital_app.py`
2. **Browser Console**: Press F12 in your browser and check for JavaScript errors
3. **Restart**: Try stopping the application (Ctrl+C) and running it again
4. **Clear Browser Cache**: Refresh the page with Ctrl+F5 (or Cmd+Shift+R on Mac)

## 🎉 You're Ready!

The Hospital Simulation Dashboard is now running! Experiment with different configurations and observe how changes affect patient flow and hospital efficiency.

### Quick Test:
1. Go to http://localhost:5002/
2. Click "⚙️ Settings" and try changing the hospital beds to 50
3. Click "💾 Save Settings"
4. Click "▶ Start Simulation"
5. Watch the real-time visualization!

Happy simulating! 🏥📊