// Socket.IO connection
const socket = io();

// DOM elements
const elements = {
    startBtn: document.getElementById('startBtn'),
    stopBtn: document.getElementById('stopBtn'),
    resetBtn: document.getElementById('resetBtn'),
    settingsBtn: document.getElementById('settingsBtn'),
    simTime: document.getElementById('simTime'),
    connectionStatus: document.getElementById('connectionStatus'),
    eventsLog: document.getElementById('eventsLog'),
    
    // Settings Modal
    settingsModal: document.getElementById('settingsModal'),
    closeBtn: document.querySelector('.close'),
    saveSettingsBtn: document.getElementById('saveSettings'),
    resetDefaultsBtn: document.getElementById('resetDefaults'),
    
    // Statistics
    totalPatients: document.getElementById('totalPatients'),
    criticalPatients: document.getElementById('criticalPatients'),
    normalPatients: document.getElementById('normalPatients'),
    avgWaitTime: document.getElementById('avgWaitTime'),
    bedOccupancy: document.getElementById('bedOccupancy'),
    providerUtil: document.getElementById('providerUtil'),
    
    // Queues
    firstVisitQueue: document.getElementById('firstVisitQueue'),
    slaDailyQueue: document.getElementById('slaDailyQueue'),
    criticalQueue: document.getElementById('criticalQueue'),
    normalFastQueue: document.getElementById('normalFastQueue'),
    normalQueue: document.getElementById('normalQueue'),
    
    // Patient tracking
    patientSearch: document.getElementById('patientSearch'),
    searchBtn: document.getElementById('searchBtn'),
    patientFilter: document.getElementById('patientFilter'),
    patientList: document.getElementById('patientList')
};

// Chart configurations
let charts = {};
let chartData = {
    waitTimes: {
        labels: [],
        data: []
    },
    patientFlow: {
        labels: [],
        arrivals: [],
        discharges: []
    },
    providerUtil: {
        labels: [],
        data: []
    }
};

// Patient tracking data
let allPatients = [];
let filteredPatients = [];
let currentFilter = 'all';
let searchTerm = '';

// Initialize charts
function initializeCharts() {
    // Wait Time Chart
    const waitTimeCtx = document.getElementById('waitTimeChart').getContext('2d');
    charts.waitTime = new Chart(waitTimeCtx, {
        type: 'line',
        data: {
            labels: chartData.waitTimes.labels,
            datasets: [{
                label: 'Average Wait Time (minutes)',
                data: chartData.waitTimes.data,
                borderColor: '#667eea',
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
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Minutes'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Simulation Time'
                    }
                }
            }
        }
    });

    // Patient Flow Chart
    const patientFlowCtx = document.getElementById('patientFlowChart').getContext('2d');
    charts.patientFlow = new Chart(patientFlowCtx, {
        type: 'bar',
        data: {
            labels: chartData.patientFlow.labels,
            datasets: [
                {
                    label: 'Arrivals',
                    data: chartData.patientFlow.arrivals,
                    backgroundColor: 'rgba(39, 174, 96, 0.8)',
                    borderColor: '#27ae60',
                    borderWidth: 1
                },
                {
                    label: 'Discharges',
                    data: chartData.patientFlow.discharges,
                    backgroundColor: 'rgba(231, 76, 60, 0.8)',
                    borderColor: '#e74c3c',
                    borderWidth: 1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Number of Patients'
                    }
                }
            }
        }
    });

    // Provider Utilization Chart
    const providerCtx = document.getElementById('providerChart').getContext('2d');
    charts.provider = new Chart(providerCtx, {
        type: 'doughnut',
        data: {
            labels: ['Busy', 'Available'],
            datasets: [{
                data: [0, 100],
                backgroundColor: [
                    'rgba(231, 76, 60, 0.8)',
                    'rgba(39, 174, 96, 0.8)'
                ],
                borderColor: [
                    '#e74c3c',
                    '#27ae60'
                ],
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

// Event handlers
elements.startBtn.addEventListener('click', () => {
    socket.emit('start_simulation');
    elements.startBtn.disabled = true;
    elements.stopBtn.disabled = false;
});

elements.stopBtn.addEventListener('click', () => {
    socket.emit('stop_simulation');
    elements.startBtn.disabled = false;
    elements.stopBtn.disabled = true;
});

elements.resetBtn.addEventListener('click', () => {
    socket.emit('reset_simulation');
    elements.startBtn.disabled = false;
    elements.stopBtn.disabled = true;
    resetDashboard();
});

// Patient tracking event handlers
elements.searchBtn.addEventListener('click', () => {
    searchTerm = elements.patientSearch.value.trim();
    filterAndDisplayPatients();
});

elements.patientSearch.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        searchTerm = elements.patientSearch.value.trim();
        filterAndDisplayPatients();
    }
});

elements.patientFilter.addEventListener('change', () => {
    currentFilter = elements.patientFilter.value;
    filterAndDisplayPatients();
});


// Socket event handlers
socket.on('connect', () => {
    elements.connectionStatus.textContent = '● Connected';
    elements.connectionStatus.className = 'connection-status connected';
    addEvent('System', 'Connected to simulation server', 'system');
});

socket.on('disconnect', () => {
    elements.connectionStatus.textContent = '● Disconnected';
    elements.connectionStatus.className = 'connection-status disconnected';
    addEvent('System', 'Disconnected from simulation server', 'system');
});

socket.on('status', (data) => {
    addEvent('System', data.message, 'system');
});

socket.on('dashboard_update', (data) => {
    updateDashboard(data);
});

socket.on('patient_arrival', (data) => {
    addEvent(data.time, `Patient ${data.patient_id} arrived (${data.status})`, 'arrival');
    updatePatientFlowChart('arrival');
});

socket.on('patient_dispatched', (data) => {
    const waitMinutes = Math.round(data.wait_time);
    addEvent(data.time, `Patient ${data.patient_id} dispatched to ${data.provider_name} (waited ${waitMinutes}min)`, 'dispatch');
});

socket.on('service_started', (data) => {
    const serviceMinutes = Math.round(data.service_time);
    addEvent(data.time, `${data.provider_name} started treating Patient ${data.patient_id} (${serviceMinutes}min)`, 'service');
});

socket.on('service_completed', (data) => {
    addEvent(data.time, `${data.provider_name} completed treating Patient ${data.patient_id} (Visit #${data.visit_number})`, 'service');
});

socket.on('patient_discharged', (data) => {
    const avgWait = Math.round(data.avg_wait_time);
    const days = Math.round(data.days_in_hospital * 10) / 10;
    addEvent(data.time, `Patient ${data.patient_id} discharged (${data.total_visits} visits, ${avgWait}min avg wait, ${days} days)`, 'discharge');
    updatePatientFlowChart('discharge');
});

socket.on('status_change', (data) => {
    addEvent(data.time, `Patient ${data.patient_id} status changed from ${data.old_status} to ${data.new_status}`, 'status');
});

socket.on('patient_fast_tracked', (data) => {
    addEvent(data.time, `Patient ${data.patient_id} fast-tracked: ${data.reason}`, 'status');
});

socket.on('patient_sla_promoted', (data) => {
    addEvent(data.time, `Patient ${data.patient_id} SLA promoted: ${data.reason}`, 'status');
});

socket.on('simulation_complete', (data) => {
    addEvent('System', `Simulation completed. Total patients served: ${data.total_patients_served}`, 'system');
    elements.startBtn.disabled = false;
    elements.stopBtn.disabled = true;
});

socket.on('reset_dashboard', () => {
    resetDashboard();
});

socket.on('patient_list_update', (data) => {
    allPatients = [...data.active_patients, ...data.discharged_patients];
    filterAndDisplayPatients();
});


// Dashboard update functions
function updateDashboard(data) {
    // Update simulation time
    elements.simTime.textContent = data.time;
    
    // Update statistics
    elements.totalPatients.textContent = data.total_patients;
    elements.criticalPatients.textContent = data.critical_patients;
    elements.normalPatients.textContent = data.normal_patients;
    elements.avgWaitTime.textContent = Math.round(data.avg_current_wait);
    elements.bedOccupancy.textContent = Math.round(data.bed_occupancy * 100) + '%';
    elements.providerUtil.textContent = Math.round(data.provider_utilization * 100) + '%';
    
    // Update queue status
    elements.firstVisitQueue.textContent = data.queue_sizes.first_visit;
    elements.slaDailyQueue.textContent = data.queue_sizes.sla_daily;
    elements.criticalQueue.textContent = data.queue_sizes.critical;
    elements.normalFastQueue.textContent = data.queue_sizes.normal_fast;
    elements.normalQueue.textContent = data.queue_sizes.normal;
    
    // Update charts
    updateWaitTimeChart(data.time, data.avg_current_wait);
    updateProviderChart(data.provider_utilization);
}

function updateWaitTimeChart(time, waitTime) {
    const maxPoints = 20; // Keep last 20 data points
    
    chartData.waitTimes.labels.push(time);
    chartData.waitTimes.data.push(Math.round(waitTime));
    
    if (chartData.waitTimes.labels.length > maxPoints) {
        chartData.waitTimes.labels.shift();
        chartData.waitTimes.data.shift();
    }
    
    charts.waitTime.update('none'); // No animation for real-time updates
}

function updatePatientFlowChart(type) {
    const currentHour = chartData.patientFlow.labels.length;
    const label = `Hour ${currentHour + 1}`;
    
    // Ensure we have data arrays for current hour
    if (chartData.patientFlow.labels.length === 0 || 
        chartData.patientFlow.labels[chartData.patientFlow.labels.length - 1] !== label) {
        chartData.patientFlow.labels.push(label);
        chartData.patientFlow.arrivals.push(0);
        chartData.patientFlow.discharges.push(0);
    }
    
    const lastIndex = chartData.patientFlow.labels.length - 1;
    
    if (type === 'arrival') {
        chartData.patientFlow.arrivals[lastIndex]++;
    } else if (type === 'discharge') {
        chartData.patientFlow.discharges[lastIndex]++;
    }
    
    // Keep last 12 hours
    const maxPoints = 12;
    if (chartData.patientFlow.labels.length > maxPoints) {
        chartData.patientFlow.labels.shift();
        chartData.patientFlow.arrivals.shift();
        chartData.patientFlow.discharges.shift();
    }
    
    charts.patientFlow.update('none');
}

function updateProviderChart(utilization) {
    const utilizationPercent = Math.round(utilization * 100);
    const availablePercent = 100 - utilizationPercent;
    
    charts.provider.data.datasets[0].data = [utilizationPercent, availablePercent];
    charts.provider.update('none');
}

function addEvent(time, message, type) {
    const eventDiv = document.createElement('div');
    eventDiv.className = `event-item event-${type}`;
    
    let statusIndicator = '';
    if (message.includes('critical')) {
        statusIndicator = '<span class="status-indicator status-critical"></span>';
    } else if (message.includes('normal')) {
        statusIndicator = '<span class="status-indicator status-normal"></span>';
    }
    
    eventDiv.innerHTML = `
        <span class="event-time">${time}:</span> ${statusIndicator}${message}
    `;
    
    elements.eventsLog.insertBefore(eventDiv, elements.eventsLog.firstChild);
    
    // Keep only last 50 events
    const events = elements.eventsLog.children;
    if (events.length > 50) {
        elements.eventsLog.removeChild(events[events.length - 1]);
    }
}

function resetDashboard() {
    // Reset all statistics
    elements.totalPatients.textContent = '0';
    elements.criticalPatients.textContent = '0';
    elements.normalPatients.textContent = '0';
    elements.avgWaitTime.textContent = '0';
    elements.bedOccupancy.textContent = '0%';
    elements.providerUtil.textContent = '0%';
    
    // Reset queue status
    elements.firstVisitQueue.textContent = '0';
    elements.slaDailyQueue.textContent = '0';
    elements.criticalQueue.textContent = '0';
    elements.normalFastQueue.textContent = '0';
    elements.normalQueue.textContent = '0';
    
    // Reset simulation time
    elements.simTime.textContent = 'Simulation Stopped';
    
    // Clear events log
    elements.eventsLog.innerHTML = '<div class="event-item"><span class="event-time">System:</span> Dashboard reset</div>';
    
    // Reset chart data
    chartData.waitTimes.labels = [];
    chartData.waitTimes.data = [];
    chartData.patientFlow.labels = [];
    chartData.patientFlow.arrivals = [];
    chartData.patientFlow.discharges = [];
    
    // Update charts
    charts.waitTime.update();
    charts.patientFlow.update();
    charts.provider.data.datasets[0].data = [0, 100];
    charts.provider.update();
    
    // Reset patient tracking
    resetPatientTracking();
}

// Patient tracking functions
function filterAndDisplayPatients() {
    // Filter patients based on current filter and search term
    filteredPatients = allPatients.filter(patient => {
        // Filter by status/type
        let passesFilter = true;
        switch (currentFilter) {
            case 'active':
                passesFilter = patient.in_system;
                break;
            case 'critical':
                passesFilter = patient.status === 'critical';
                break;
            case 'normal':
                passesFilter = patient.status === 'normal';
                break;
            case 'discharged':
                passesFilter = !patient.in_system;
                break;
            default: // 'all'
                passesFilter = true;
        }
        
        // Filter by search term
        if (searchTerm && passesFilter) {
            passesFilter = patient.pid.toString().includes(searchTerm) ||
                          patient.status.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          patient.current_state.toLowerCase().includes(searchTerm.toLowerCase());
        }
        
        return passesFilter;
    });
    
    displayPatients();
}

function displayPatients() {
    // Clear existing patient items (except header)
    const existingItems = elements.patientList.querySelectorAll('.patient-item');
    existingItems.forEach(item => item.remove());
    
    // Sort patients by criticality (critical first), then by patient ID
    const sortedPatients = [...filteredPatients].sort((a, b) => {
        // Critical patients first
        if (a.status === 'critical' && b.status !== 'critical') return -1;
        if (a.status !== 'critical' && b.status === 'critical') return 1;
        
        // Within same criticality, sort by current wait time (longest first)
        if (a.status === b.status) {
            return b.current_wait_time - a.current_wait_time;
        }
        
        return 0;
    });
    
    // Add patient items
    sortedPatients.forEach(patient => {
        const patientItem = createPatientItem(patient);
        elements.patientList.appendChild(patientItem);
    });
}

function createPatientItem(patient) {
    const container = document.createElement('div');
    container.className = 'patient-item';
    
    const statusClass = `patient-status-${patient.status}`;
    const stateClass = `patient-state-${patient.current_state}`;
    
    // Format wait times
    const currentWait = Math.round(patient.current_wait_time);
    const totalWait = Math.round(patient.total_wait_time);
    
    // Format location
    let location = 'Bed';
    if (patient.current_queue) {
        location = `Queue: ${patient.current_queue}`;
    } else if (patient.current_provider) {
        location = `With: ${patient.current_provider}`;
    } else if (!patient.in_system) {
        location = 'Discharged';
    }
    
    container.innerHTML = `
        <div>${patient.pid}</div>
        <div class="${statusClass}">${patient.status}</div>
        <div class="${stateClass}">${patient.current_state}</div>
        <div>${currentWait}m</div>
        <div>${totalWait}m</div>
        <div>${patient.num_visits}</div>
        <div>${location}</div>
    `;
    
    return container;
}


function resetPatientTracking() {
    allPatients = [];
    filteredPatients = [];
    searchTerm = '';
    currentFilter = 'all';
    elements.patientSearch.value = '';
    elements.patientFilter.value = 'all';
    
    // Clear patient list
    const existingItems = elements.patientList.querySelectorAll('.patient-item');
    existingItems.forEach(item => item.remove());
}

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

// Settings Modal Events
if (elements.settingsBtn) {
    elements.settingsBtn.addEventListener('click', () => {
        loadSettingsToForm();
        elements.settingsModal.style.display = 'block';
    });
}

if (elements.closeBtn) {
    elements.closeBtn.addEventListener('click', () => {
        elements.settingsModal.style.display = 'none';
    });
}

window.addEventListener('click', (event) => {
    if (event.target === elements.settingsModal) {
        elements.settingsModal.style.display = 'none';
    }
});

if (elements.saveSettingsBtn) {
    elements.saveSettingsBtn.addEventListener('click', () => {
        const newConfig = getSettingsFromForm();
        socket.emit('update_config', newConfig);
    });
}

if (elements.resetDefaultsBtn) {
    elements.resetDefaultsBtn.addEventListener('click', () => {
        resetToDefaults();
    });
}

// Configuration event handlers
socket.on('config_data', function(config) {
    currentConfig = config;
    loadSettingsToForm();
    // Update bed display if needed
    if (elements.bedOccupancy) {
        const current = elements.bedOccupancy.textContent.split('/')[0];
        elements.bedOccupancy.textContent = `${current}/${config.hospital_beds}`;
    }
});

socket.on('config_updated', function(response) {
    if (response.success) {
        currentConfig = response.config;
        addEvent('System', 'Settings updated successfully!', 'system');
        elements.settingsModal.style.display = 'none';
        
        // Update bed display
        if (elements.bedOccupancy) {
            const current = elements.bedOccupancy.textContent.split('/')[0];
            elements.bedOccupancy.textContent = `${current}/${currentConfig.hospital_beds}`;
        }
    } else {
        addEvent('System', `Settings update failed: ${response.error}`, 'error');
    }
});

// Initialize everything when page loads
document.addEventListener('DOMContentLoaded', () => {
    initializeCharts();
    addEvent('System', 'Dashboard initialized and ready', 'system');
    // Request current configuration
    socket.emit('get_config');
});