"""
Simulation2 wrapper for real-time visualization based on EXACT logic from Simulation2 folder.
This is a self-contained version that copies all the necessary code directly.
"""

import random
import time

# Configuration constants copied from Simulation2/config.py
MINUTES_PER_DAY = 1440
SIM_DAYS = 28
TOTAL_MINUTES = SIM_DAYS * MINUTES_PER_DAY

# Patient parameters
BEDS = 20
N_INITIAL_PATIENTS = 18
PATIENT_SEVERITY_MIN = 1
PATIENT_SEVERITY_MAX = 100
PATIENT_INFLUX_TOTAL = SIM_DAYS * 2

# Inpatient day ranges by initial/current severity
INPATIENT_DAYS_LT50 = (3, 7)
INPATIENT_DAYS_GE50 = (3, 28)

# Staff parameters
N_PROVIDERS = 3
N_NURSES = 5
NURSES_MAX_PATIENTS = 4

# Treatment parameters
GROWTH_PER_MIN = 0.5
DECAY_PER_MIN = 0.5
SESSION_END_BUMP = 0.5
DISCHARGE_ON_SESSION_END = False
MIN_TREATMENT_TIME = 10
MAX_TREATMENT_MULTIPLIER = 2
PROVIDER_MAINTAIN_PROB_GE50 = 0.10
PROVIDER_MAINTAIN_PROB_LT50 = 0.01

# Random Effect
UPGRADE_ENABLED = True
PATIENT_SEVERITY_UPGRADE_INTERVAL = 12 * 60  # every 12 hours
PATIENT_SEVERITY_UPGRADE_PERCENT = 0.10  # 10% of <50 patients selected
PATIENT_SEVERITY_UPGRADE_FACTOR = 1.10  # increase current severity by 10%

# Random seed for reproducibility
RANDOM_SEED = 52152

def initialize_random_seeds():
    random.seed(RANDOM_SEED)

# Patient class copied from Simulation2/patient.py
class Patient:
    def __init__(self, pid, admit_time):
        self.id = pid
        self.severity = random.randint(PATIENT_SEVERITY_MIN, PATIENT_SEVERITY_MAX)
        self.initial_severity = self.severity  # Store initial severity
        self.admit_time = admit_time
        # Initial cohort (admit_time==0) get a discharge window immediately based on initial severity.
        # New patients (admit_time>0) receive a discharge window only after their first time being seen.
        if admit_time == 0:
            self.time_in_inpatient = (
                random.randint(*INPATIENT_DAYS_GE50) if self.severity >= 50 else random.randint(*INPATIENT_DAYS_LT50)
            )
        else:
            self.time_in_inpatient = None
        self.discharge_time = None
        self.discharge_reason = None
        self.seen = 0  # 1 if seen, 0 if not
        self.assigned_staff = None
        self.maintain = None
        self.treatment_minutes_left = 0
        self.waiting_time = 0
        self.total_time_in_hospital = 0
        self.waiting_periods = []  # List of waiting period lengths (in minutes)
        self._current_wait = 0
        self.first_seen_time = None
        self.cumulative_waiting_time = 0  # Track total time waiting for squared growth
        self.total_treatment_time = 0  # Track total time being treated

    def start_waiting(self):
        if self._current_wait == 0:
            self._current_wait = 1
        else:
            self._current_wait += 1

    def stop_waiting(self):
        if self._current_wait > 0:
            self.waiting_periods.append(self._current_wait)
            self._current_wait = 0

    def to_dict(self):
        avg_wait = (sum(self.waiting_periods) / len(self.waiting_periods)) if self.waiting_periods else 0
        return {
            'id': self.id,
            'initial_severity': self.initial_severity,
            'severity': self.severity,
            'admit_time': self.admit_time,
            'time_in_inpatient_days': self.time_in_inpatient if self.time_in_inpatient is not None else 0,
            'discharge_time': self.discharge_time,
            'discharge_reason': self.discharge_reason,
            'seen': self.seen,
            'assigned_staff': self.assigned_staff,
            'maintain': self.maintain,
            'waiting_time': self.waiting_time,
            'total_time_in_hospital': self.total_time_in_hospital,
            'average_waiting_period': avg_wait,
            'waiting_periods': self.waiting_periods
        }

# Staff classes copied from Simulation2/staff.py
class Provider:
    def __init__(self, pid):
        self.id = f'provider_{pid}'
        self.available = True
        self.current_patient = None
        self.type = 'provider'

class Nurse:
    def __init__(self, nid):
        self.id = f'nurse_{nid}'
        self.available = True
        self.current_patient = None
        self.type = 'nurse'
        self.assigned_patients = []  # List of patient ids (strings)

def initialize_staff():
    providers = [Provider(i+1) for i in range(N_PROVIDERS)]
    nurses = [Nurse(i+1) for i in range(N_NURSES)]
    return providers, nurses

class Simulation2Wrapper:
    def __init__(self, socketio, config=None):
        self.socketio = socketio
        self.running = False
        
        # Apply configuration parameters
        if config:
            global BEDS, N_INITIAL_PATIENTS, SIM_DAYS, TOTAL_MINUTES, N_PROVIDERS, N_NURSES, NURSES_MAX_PATIENTS, PATIENT_INFLUX_TOTAL
            BEDS = config['hospital_beds']
            N_INITIAL_PATIENTS = config['initial_patients']
            SIM_DAYS = config['simulation_weeks'] * 7
            TOTAL_MINUTES = SIM_DAYS * MINUTES_PER_DAY
            N_PROVIDERS = config['num_doctors']
            N_NURSES = config['num_nurses']
            NURSES_MAX_PATIENTS = config['nurses_max_patients']
            PATIENT_INFLUX_TOTAL = SIM_DAYS * 2 * config['patient_influx_per_12h']
            self.SIM_SPEED = config['simulation_speed']
        else:
            self.SIM_SPEED = 50
        
        # Initialize exactly like the original Simulation class
        initialize_random_seeds()
        self.patients = []
        self.providers, self.nurses = initialize_staff()
        self.time = 0
        self.next_patient_id = 1
        self.influx_patients_to_add = PATIENT_INFLUX_TOTAL
        
        # Schedule one influx per 12-hour block at a random minute inside the block
        block = PATIENT_SEVERITY_UPGRADE_INTERVAL
        self.influx_times = []
        for b in range(SIM_DAYS * 2):
            start = b * block
            end = start + block
            self.influx_times.append(random.randrange(start, min(end, TOTAL_MINUTES)))
        self.influx_times = sorted(t for t in self.influx_times if 0 < t < TOTAL_MINUTES)
        self.waiting_times = {}

    def add_patient(self, admit_time):
        if sum(1 for p in self.patients if p.discharge_time is None) >= BEDS:
            return None  # No bed available
        patient = Patient(f"patient_{self.next_patient_id}", admit_time)
        self.patients.append(patient)
        self.next_patient_id += 1
        return patient

    def assign_nurse_panels(self):
        # Assign nurse panels in consecutive blocks of 4 patient IDs by integer suffix
        # Example: patients 1-4 -> nurse_1, 5-8 -> nurse_2, etc.
        panels = {n.id: [] for n in self.nurses}
        patient_ids = [p.id for p in self.patients]
        n_nurses = len(self.nurses)
        # Assign 4 patients per nurse, and if there are extra patients, assign them to nurses in order
        for i, pid in enumerate(patient_ids):
            nurse_idx = i // NURSES_MAX_PATIENTS
            if nurse_idx >= n_nurses:
                # Overflow: assign extra patients to nurses in round-robin fashion
                nurse_idx = i % n_nurses
            nurse = self.nurses[nurse_idx]
            panels[nurse.id].append(pid)
        for n in self.nurses:
            n.assigned_patients = panels.get(n.id, [])

    def emit_real_time_update(self):
        """Emit real-time data to the dashboard"""
        if not self.running:
            return
            
        # Prepare patient data for visualization
        patient_data = []
        for patient in self.patients:
            if patient.discharge_time is None:  # Only active patients
                # Show current waiting period, not total waiting time
                current_wait = patient._current_wait if patient.seen == 0 else 0
                patient_info = {
                    'id': patient.id,
                    'severity': round(patient.severity, 2),
                    'initial_severity': patient.initial_severity,
                    'waiting_time': current_wait,  # Show current waiting period, not total
                    'seen': patient.seen,
                    'assigned_staff': patient.assigned_staff,
                    'treatment_minutes_left': patient.treatment_minutes_left,
                    'total_time_in_hospital': patient.total_time_in_hospital,
                    'admit_time': patient.admit_time,
                    'time_in_inpatient': patient.time_in_inpatient,
                    'maintain': patient.maintain
                }
                patient_data.append(patient_info)
        
        # Sort by severity descending for display
        patient_data.sort(key=lambda p: p['severity'], reverse=True)
        
        # Prepare staff data
        staff_data = []
        for staff in self.providers + self.nurses:
            staff_info = {
                'id': staff.id,
                'type': staff.type,
                'available': staff.available,
                'current_patient': staff.current_patient,
                'assigned_patients': getattr(staff, 'assigned_patients', [])
            }
            staff_data.append(staff_info)
        
        # Calculate summary statistics
        active_patients = [p for p in self.patients if p.discharge_time is None]
        total_active = len(active_patients)
        avg_severity = sum(p.severity for p in active_patients) / total_active if total_active > 0 else 0
        
        # Calculate average waiting period (like in original report), not total waiting time
        avg_waiting_periods = []
        for p in active_patients:
            if p.waiting_periods:
                avg_wait = sum(p.waiting_periods) / len(p.waiting_periods)
                avg_waiting_periods.append(avg_wait)
        avg_waiting_time = sum(avg_waiting_periods) / len(avg_waiting_periods) if avg_waiting_periods else 0
        
        # Beds occupancy
        beds_occupied = total_active
        beds_available = BEDS - beds_occupied
        
        summary = {
            'current_time': self.time,
            'current_day': self.time // MINUTES_PER_DAY + 1,
            'current_hour': (self.time % MINUTES_PER_DAY) // 60,
            'current_minute': self.time % 60,
            'total_patients': len(self.patients),
            'active_patients': total_active,
            'beds_occupied': beds_occupied,
            'beds_available': beds_available,
            'avg_severity': round(avg_severity, 2),
            'avg_waiting_time': round(avg_waiting_time, 2),
            'total_discharged': sum(1 for p in self.patients if p.discharge_time is not None)
        }
        
        # Emit the update
        self.socketio.emit('simulation2_update', {
            'patients': patient_data,
            'staff': staff_data,
            'summary': summary
        })

    def run(self):
        """EXACT copy of the original run() method with real-time tracking added"""
        self.running = True
        
        # Initialize patients
        for _ in range(N_INITIAL_PATIENTS):
            self.add_patient(0)
        # Build initial nurse panels
        self.assign_nurse_panels()
        
        # Emit initial state
        self.emit_real_time_update()

        # Main simulation loop
        for t in range(TOTAL_MINUTES):
            if not self.running:
                break
                
            self.time = t

            # Add influx patients at random times per block if beds available
            while self.influx_times and t == self.influx_times[0]:
                if sum(1 for p in self.patients if p.discharge_time is None) < BEDS:
                    self.add_patient(t)
                    # Nurse panels may grow; reassign panels to include new ID
                    self.assign_nurse_panels()
                self.influx_times.pop(0)

            # Every 12 hours, upgrade 10% of <50 severity patients multiplicatively by 10%
            if UPGRADE_ENABLED and t > 0 and t % PATIENT_SEVERITY_UPGRADE_INTERVAL == 0:
                lt50 = [p for p in self.patients if p.severity < 50 and p.discharge_time is None]
                n_upgrade = max(1, int(PATIENT_SEVERITY_UPGRADE_PERCENT * len(lt50)))
                upgrade_patients = random.sample(lt50, n_upgrade) if lt50 and n_upgrade > 0 else []
                for p in upgrade_patients:
                    p.severity = min(PATIENT_SEVERITY_MAX, max(PATIENT_SEVERITY_MIN, round(p.severity * PATIENT_SEVERITY_UPGRADE_FACTOR, 2)))

            # Remove discharged patients from assignment consideration
            active_patients = [p for p in self.patients if p.discharge_time is None]

            # Free up staff who finished treatment
            for staff in self.providers + self.nurses:
                if staff.current_patient is not None:
                    patient = next((p for p in self.patients if p.id == staff.current_patient), None)
                    if patient and patient.treatment_minutes_left <= 0:
                        # Treatment session ended
                        # Optionally discharge immediately upon session end
                        if DISCHARGE_ON_SESSION_END:
                            patient.discharge_time = t
                            patient.discharge_reason = 'session_end'
                            patient.stop_waiting()
                            # Free staff and clear assignment
                            staff.available = True
                            staff.current_patient = None
                            patient.seen = 0
                            patient.assigned_staff = None
                            # Do not apply end-of-session bump if patient leaves immediately
                            patient.maintain = None
                        else:
                            # Free staff and clear assignment; patient stays admitted
                            staff.available = True
                            staff.current_patient = None
                            patient.seen = 0
                            patient.assigned_staff = None
                            # Apply configurable end-of-session bump (preserve prior behavior)
                            if patient.maintain is not None and patient.treatment_minutes_left == 0:
                                patient.severity = min(PATIENT_SEVERITY_MAX, patient.severity + SESSION_END_BUMP)
                                patient.maintain = None
                        # No explicit cooldown: prioritization handled by severity sorting and staff availability

            # Accumulate waiting time for all active patients not currently being seen
            # Per config: linear growth: +GROWTH_PER_MIN per minute when waiting
            for patient in active_patients:
                if patient.seen == 0 and patient.discharge_time is None:
                    patient.waiting_time += 1
                    patient.start_waiting()
                    # Apply linear growth
                    patient.severity = min(PATIENT_SEVERITY_MAX, patient.severity + GROWTH_PER_MIN)

            # Sort by severity descending (prioritize high severity)
            active_patients.sort(key=lambda p: p.severity, reverse=True)

            # For each patient, process logic
            for patient in active_patients:
                # Skip if already discharged (should not happen in active_patients, but safety check)
                if patient.discharge_time is not None:
                    continue
                # If patient is already assigned to staff
                if patient.seen == 1:
                    # If just started being seen, stop waiting period
                    patient.stop_waiting()
                    # Continue treatment
                    if patient.treatment_minutes_left > 0:
                        patient.treatment_minutes_left -= 1
                        patient.total_treatment_time += 1  # Track treatment time
                        # If maintain=0, apply linear decay (decay rate based on initial severity)
                        if patient.maintain == 0:
                            decay_rate = 0.25 if patient.initial_severity >= 50 else DECAY_PER_MIN
                            patient.severity = max(PATIENT_SEVERITY_MIN, patient.severity - decay_rate)
                        # If maintain=1, severity stays the same
                        # If treatment ends now, will be freed next loop
                    else:
                        # Treatment just ended, will be freed above
                        pass
                else:
                    # Not seen
                    # Try to assign provider first, then nurse within panel
                    assigned = False
                    for staff in self.providers + self.nurses:
                        # Enforce nurse panel: nurse can see only their assigned patients
                        if not staff.available:
                            continue
                        if staff.type == 'nurse' and patient.id not in getattr(staff, 'assigned_patients', []):
                            continue
                        # Assign staff to patient
                        staff.available = False
                        staff.current_patient = patient.id
                        patient.seen = 1
                        patient.assigned_staff = staff.id
                        # First time being seen? set timestamp and inpatient window for new admissions
                        if patient.first_seen_time is None:
                            patient.first_seen_time = t
                            if patient.admit_time > 0:
                                # Assign discharge window for new patients when first seen
                                days = random.randint(*INPATIENT_DAYS_GE50) if patient.severity >= 50 else random.randint(*INPATIENT_DAYS_LT50)
                                patient.time_in_inpatient = days
                        # Determine maintain probability and treatment duration by staff type
                        prob = PROVIDER_MAINTAIN_PROB_GE50 if patient.severity >= 50 else PROVIDER_MAINTAIN_PROB_LT50
                        patient.maintain = 1 if random.random() < prob else 0
                        # Max treatment time per session: random between MIN and (initial_severity * MAX_MULTIPLIER)
                        # Session duration now depends on CURRENT severity at assignment time
                        max_treatment = int(max(PATIENT_SEVERITY_MIN, patient.severity) * MAX_TREATMENT_MULTIPLIER)
                        patient.treatment_minutes_left = random.randint(MIN_TREATMENT_TIME, max(MIN_TREATMENT_TIME, max_treatment))
                        assigned = True
                        # Just assigned, stop waiting period
                        patient.stop_waiting()
                        break
                    # If not assigned, severity has already grown in the waiting accumulation loop above
                    # No additional severity change needed here

                # Update patient time in hospital first
                patient.total_time_in_hospital += 1

                # Discharge logic - check if patient has reached their discharge window
                # Only discharge if they have a discharge window assigned (initial patients or patients who have been seen)
                if patient.time_in_inpatient is not None:
                    time_in_hospital_days = (t - patient.admit_time) / MINUTES_PER_DAY
                    if time_in_hospital_days >= patient.time_in_inpatient:
                        patient.discharge_time = t
                        patient.discharge_reason = 'natural'
                        # Stop any active waiting period immediately upon discharge
                        patient.stop_waiting()
                        # Free up staff if patient was being seen
                        if patient.seen == 1 and patient.assigned_staff:
                            for staff in self.providers + self.nurses:
                                if staff.id == patient.assigned_staff:
                                    staff.available = True
                                    staff.current_patient = None
                                    # If nurse, immediately assign to another waiting patient without a nurse
                                    if staff.type == 'nurse':
                                        # Find a waiting patient not assigned to any nurse
                                        for p in self.patients:
                                            if p.discharge_time is None and p.seen == 0 and p.assigned_staff is None and p.id in staff.assigned_patients:
                                                staff.available = False
                                                staff.current_patient = p.id
                                                p.seen = 1
                                                p.assigned_staff = staff.id
                                                # First time being seen? set timestamp and inpatient window for new admissions
                                                if p.first_seen_time is None:
                                                    p.first_seen_time = t
                                                    if p.admit_time > 0:
                                                        days = random.randint(*INPATIENT_DAYS_GE50) if p.severity >= 50 else random.randint(*INPATIENT_DAYS_LT50)
                                                        p.time_in_inpatient = days
                                                # Determine maintain probability and treatment duration by staff type
                                                prob = PROVIDER_MAINTAIN_PROB_GE50 if p.severity >= 50 else PROVIDER_MAINTAIN_PROB_LT50
                                                p.maintain = 1 if random.random() < prob else 0
                                                max_treatment = int(max(PATIENT_SEVERITY_MIN, p.severity) * MAX_TREATMENT_MULTIPLIER)
                                                p.treatment_minutes_left = random.randint(MIN_TREATMENT_TIME, max(MIN_TREATMENT_TIME, max_treatment))
                                                p.stop_waiting()
                                                break
                                    break
                            patient.seen = 0
                            patient.assigned_staff = None
                        continue  # Skip further processing for this patient

            # Emit real-time updates every few minutes for performance
            if t % 60 == 0:  # Every 60 simulation minutes (1 hour)
                self.emit_real_time_update()
                # Add small delay for real-time visualization
                time.sleep(0.1 / self.SIM_SPEED)

        # Final update
        self.emit_real_time_update()
        self.socketio.emit('simulation2_complete')

    def stop(self):
        """Stop the simulation"""
        self.running = False

    def get_waiting_time_report(self):
        """EXACT copy of the original method"""
        report = []
        for patient in self.patients:
            if patient.discharge_time is not None:
                avg_wait = (sum(patient.waiting_periods) / len(patient.waiting_periods)) if patient.waiting_periods else 0
                total_treatment_time = getattr(patient, 'total_treatment_time', 0)
                report.append({
                    'patient_id': patient.id,
                    'initial_severity': getattr(patient, 'initial_severity', patient.severity),
                    'final_severity': patient.severity,
                    'waiting_time_minutes': patient.waiting_time,
                    'waiting_time_days': patient.waiting_time / MINUTES_PER_DAY,
                    'treatment_time_minutes': total_treatment_time,
                    'treatment_time_days': total_treatment_time / MINUTES_PER_DAY,
                    'average_waiting_period_minutes': avg_wait,
                    'average_waiting_period_days': avg_wait / MINUTES_PER_DAY if avg_wait else 0,
                    'n_waiting_periods': len(patient.waiting_periods),
                    'waiting_periods': patient.waiting_periods
                })
        return report