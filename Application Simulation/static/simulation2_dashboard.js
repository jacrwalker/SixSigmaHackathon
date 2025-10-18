// Simulation2 Dashboard JavaScript
const socket = io();

// UI Elements
const startBtn = document.getElementById('startBtn');
const stopBtn = document.getElementById('stopBtn');
const resetBtn = document.getElementById('resetBtn');
const settingsBtn = document.getElementById('settingsBtn');
const statusDiv = document.getElementById('status');
const patientList = document.getElementById('patientList');

// Settings Modal Elements
const settingsModal = document.getElementById('settingsModal');
const closeBtn = document.querySelector('.close');
const saveSettingsBtn = document.getElementById('saveSettings');
const resetDefaultsBtn = document.getElementById('resetDefaults');

// Status elements
const currentTimeEl = document.getElementById('currentTime');
const currentDayEl = document.getElementById('currentDay');
const activePatientsEl = document.getElementById('activePatients');
const avgSeverityEl = document.getElementById('avgSeverity');
const bedsOccupiedEl = document.getElementById('bedsOccupied');
const avgWaitTimeEl = document.getElementById('avgWaitTime');
const totalDischargedEl = document.getElementById('totalDischarged');

// Charts
let severityChart;
let severityTrendChart;
let severityTrendData = [];

// Settings management
let currentConfig = {
    hospital_beds: 20,
    initial_patients: 18,
    simulation_weeks: 4,
    num_doctors: 3,
    num_nurses: 5,
    nurses_max_patients: 4,
    patient_influx_per_12h: 1,
    simulation_speed: 100
};

// Initialize charts
function initializeCharts() {
    // Severity Distribution Chart
    const severityCtx = document.getElementById('severityChart').getContext('2d');
    severityChart = new Chart(severityCtx, {
        type: 'bar',
        data: {
            labels: ['0-20', '21-40', '41-60', '61-80', '81-100'],
            datasets: [{
                label: 'Number of Patients',
                data: [0, 0, 0, 0, 0],
                backgroundColor: [
                    'rgba(46, 213, 115, 0.8)',
                    'rgba(255, 165, 2, 0.8)',
                    'rgba(255, 99, 72, 0.8)',
                    'rgba(255, 71, 87, 0.8)',
                    'rgba(196, 69, 105, 0.8)'
                ],
                borderColor: [
                    'rgba(46, 213, 115, 1)',
                    'rgba(255, 165, 2, 1)',
                    'rgba(255, 99, 72, 1)',
                    'rgba(255, 71, 87, 1)',
                    'rgba(196, 69, 105, 1)'
                ],
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                title: {
                    display: true,
                    text: 'Patient Severity Distribution'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    }
                }
            }
        }
    });

    // Severity Trend Chart
    const trendCtx = document.getElementById('severityTrendChart').getContext('2d');
    severityTrendChart = new Chart(trendCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Average Severity',
                data: [],
                borderColor: 'rgba(102, 126, 234, 1)',
                backgroundColor: 'rgba(102, 126, 234, 0.1)',
                borderWidth: 3,
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                title: {
                    display: true,
                    text: 'Average Severity Over Time'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        stepSize: 20
                    }
                },
                x: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Time (Hours:Minutes)'
                    }
                }
            }
        }
    });
}

// Helper function to get severity class
function getSeverityClass(severity) {
    if (severity >= 80) return 'severity-critical';
    if (severity >= 60) return 'severity-high';
    if (severity >= 40) return 'severity-medium';
    return 'severity-low';
}

// Helper function to get status class and text
function getStatusInfo(patient) {
    if (patient.seen === 1) {
        return { class: 'status-being-seen', text: 'Being Seen' };
    } else if (patient.waiting_time > 0) {
        return { class: 'status-waiting', text: 'Waiting' };
    } else {
        return { class: 'status-admitted', text: 'Admitted' };
    }
}

// Format time display
function formatTime(hour, minute) {
    return `${hour.toString().padStart(2, '0')}:${minute.toString().padStart(2, '0')}`;
}

// Update patient list
function updatePatientList(patients) {
    // Clear existing patients (keep header)
    const header = patientList.querySelector('.patient-item-header');
    patientList.innerHTML = '';
    patientList.appendChild(header);

    // Sort patients by severity (highest first)
    const sortedPatients = [...patients].sort((a, b) => b.severity - a.severity);

    sortedPatients.forEach(patient => {
        const statusInfo = getStatusInfo(patient);
        const severityClass = getSeverityClass(patient.severity);
        
        const patientEl = document.createElement('div');
        patientEl.className = 'patient-item';
        patientEl.innerHTML = `
            <div>${patient.id}</div>
            <div><span class="severity-badge ${severityClass}">${patient.severity}</span></div>
            <div>${patient.initial_severity}</div>
            <div><span class="status-badge ${statusInfo.class}">${statusInfo.text}</span></div>
            <div>${patient.waiting_time}</div>
            <div>${patient.assigned_staff || 'None'}</div>
        `;
        patientList.appendChild(patientEl);
    });
}

// Update severity distribution chart
function updateSeverityChart(patients) {
    const distribution = [0, 0, 0, 0, 0];
    
    patients.forEach(patient => {
        const severity = patient.severity;
        if (severity <= 20) distribution[0]++;
        else if (severity <= 40) distribution[1]++;
        else if (severity <= 60) distribution[2]++;
        else if (severity <= 80) distribution[3]++;
        else distribution[4]++;
    });

    severityChart.data.datasets[0].data = distribution;
    severityChart.update('none');
}

// Update severity trend chart
function updateSeverityTrend(summary) {
    const timeLabel = formatTime(summary.current_hour, summary.current_minute);
    
    // Add new data point
    severityTrendData.push({
        time: timeLabel,
        avgSeverity: summary.avg_severity
    });

    // Keep only last 50 data points for performance
    if (severityTrendData.length > 50) {
        severityTrendData.shift();
    }

    // Update chart
    severityTrendChart.data.labels = severityTrendData.map(d => d.time);
    severityTrendChart.data.datasets[0].data = severityTrendData.map(d => d.avgSeverity);
    severityTrendChart.update('none');
}

// Update status cards
function updateStatusCards(summary) {
    currentTimeEl.textContent = formatTime(summary.current_hour, summary.current_minute);
    currentDayEl.textContent = summary.current_day;
    activePatientsEl.textContent = summary.active_patients;
    avgSeverityEl.textContent = summary.avg_severity.toFixed(1);
    bedsOccupiedEl.textContent = `${summary.beds_occupied}/20`;
    avgWaitTimeEl.textContent = summary.avg_waiting_time.toFixed(1);
    totalDischargedEl.textContent = summary.total_discharged;
}

// Settings Functions
function loadSettingsToForm() {
    document.getElementById('hospital_beds').value = currentConfig.hospital_beds;
    document.getElementById('initial_patients').value = currentConfig.initial_patients;
    document.getElementById('simulation_weeks').value = currentConfig.simulation_weeks;
    document.getElementById('num_doctors').value = currentConfig.num_doctors;
    document.getElementById('num_nurses').value = currentConfig.num_nurses;
    document.getElementById('nurses_max_patients').value = currentConfig.nurses_max_patients;
    document.getElementById('patient_influx_per_12h').value = currentConfig.patient_influx_per_12h;
    document.getElementById('simulation_speed').value = currentConfig.simulation_speed;
}

function getSettingsFromForm() {
    return {
        hospital_beds: parseInt(document.getElementById('hospital_beds').value),
        initial_patients: parseInt(document.getElementById('initial_patients').value),
        simulation_weeks: parseInt(document.getElementById('simulation_weeks').value),
        num_doctors: parseInt(document.getElementById('num_doctors').value),
        num_nurses: parseInt(document.getElementById('num_nurses').value),
        nurses_max_patients: parseInt(document.getElementById('nurses_max_patients').value),
        patient_influx_per_12h: parseInt(document.getElementById('patient_influx_per_12h').value),
        simulation_speed: parseInt(document.getElementById('simulation_speed').value)
    };
}

function resetToDefaults() {
    currentConfig = {
        hospital_beds: 20,
        initial_patients: 18,
        simulation_weeks: 4,
        num_doctors: 3,
        num_nurses: 5,
        nurses_max_patients: 4,
        patient_influx_per_12h: 1,
        simulation_speed: 100
    };
    loadSettingsToForm();
}

// Event Listeners
startBtn.addEventListener('click', () => {
    socket.emit('start_simulation2');
    startBtn.disabled = true;
    stopBtn.disabled = false;
});

stopBtn.addEventListener('click', () => {
    socket.emit('stop_simulation2');
    startBtn.disabled = false;
    stopBtn.disabled = true;
});

resetBtn.addEventListener('click', () => {
    socket.emit('reset_simulation2');
    startBtn.disabled = false;
    stopBtn.disabled = true;
    
    // Reset charts
    severityTrendData = [];
    if (severityChart) {
        severityChart.data.datasets[0].data = [0, 0, 0, 0, 0];
        severityChart.update();
    }
    if (severityTrendChart) {
        severityTrendChart.data.labels = [];
        severityTrendChart.data.datasets[0].data = [];
        severityTrendChart.update();
    }
    
    // Reset status cards
    currentTimeEl.textContent = '00:00';
    currentDayEl.textContent = '1';
    activePatientsEl.textContent = '0';
    avgSeverityEl.textContent = '0.0';
    bedsOccupiedEl.textContent = `0/${currentConfig.hospital_beds}`;
    avgWaitTimeEl.textContent = '0.0';
    totalDischargedEl.textContent = '0';
    
    // Clear patient list (keep header)
    const header = patientList.querySelector('.patient-item-header');
    patientList.innerHTML = '';
    patientList.appendChild(header);
});

// Settings Modal Events
settingsBtn.addEventListener('click', () => {
    loadSettingsToForm();
    settingsModal.style.display = 'block';
});

closeBtn.addEventListener('click', () => {
    settingsModal.style.display = 'none';
});

window.addEventListener('click', (event) => {
    if (event.target === settingsModal) {
        settingsModal.style.display = 'none';
    }
});

saveSettingsBtn.addEventListener('click', () => {
    const newConfig = getSettingsFromForm();
    socket.emit('update_config', newConfig);
});

resetDefaultsBtn.addEventListener('click', () => {
    resetToDefaults();
});

// Socket Event Handlers
socket.on('connect', function() {
    statusDiv.textContent = 'Connected to server. Ready to start Simulation2...';
    statusDiv.className = 'alert';
});

socket.on('disconnect', function() {
    statusDiv.textContent = 'Disconnected from server.';
    statusDiv.className = 'alert';
});

socket.on('status2', function(data) {
    statusDiv.textContent = data.message;
});

socket.on('simulation2_update', function(data) {
    try {
        updateStatusCards(data.summary);
        updatePatientList(data.patients);
        updateSeverityChart(data.patients);
        updateSeverityTrend(data.summary);
    } catch (error) {
        console.error('Error updating dashboard:', error);
    }
});

socket.on('simulation2_complete', function() {
    statusDiv.textContent = 'Simulation2 completed successfully!';
    startBtn.disabled = false;
    stopBtn.disabled = true;
});

socket.on('reset_dashboard2', function() {
    // Reset all displays
    severityTrendData = [];
    if (severityChart) {
        severityChart.data.datasets[0].data = [0, 0, 0, 0, 0];
        severityChart.update();
    }
    if (severityTrendChart) {
        severityTrendChart.data.labels = [];
        severityTrendChart.data.datasets[0].data = [];
        severityTrendChart.update();
    }
    
    // Reset status cards
    currentTimeEl.textContent = '00:00';
    currentDayEl.textContent = '1';
    activePatientsEl.textContent = '0';
    avgSeverityEl.textContent = '0.0';
    bedsOccupiedEl.textContent = `0/${currentConfig.hospital_beds}`;
    avgWaitTimeEl.textContent = '0.0';
    totalDischargedEl.textContent = '0';
    
    // Clear patient list (keep header)
    const header = patientList.querySelector('.patient-item-header');
    patientList.innerHTML = '';
    patientList.appendChild(header);
});

// Configuration event handlers
socket.on('config_data', function(config) {
    currentConfig = config;
    loadSettingsToForm();
    // Update beds display if needed
    bedsOccupiedEl.textContent = `${bedsOccupiedEl.textContent.split('/')[0]}/${config.hospital_beds}`;
});

socket.on('config_updated', function(response) {
    if (response.success) {
        currentConfig = response.config;
        statusDiv.textContent = 'Settings updated successfully!';
        statusDiv.className = 'alert';
        settingsModal.style.display = 'none';
        
        // Update beds display
        const currentBeds = bedsOccupiedEl.textContent.split('/')[0];
        bedsOccupiedEl.textContent = `${currentBeds}/${currentConfig.hospital_beds}`;
    } else {
        statusDiv.textContent = `Settings update failed: ${response.error}`;
        statusDiv.className = 'alert';
    }
});

// Initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    initializeCharts();
    // Request current configuration
    socket.emit('get_config');
});