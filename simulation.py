import random
import numpy as np
from config import *
from patient import Patient
from staff import initialize_staff

class Simulation:
    def __init__(self):
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
        for p in self.patients:
            try:
                idx = int(p.id.split('_')[-1]) - 1
            except Exception:
                idx = 0
            nurse_idx = (idx // NURSES_MAX_PATIENTS) % len(self.nurses)
            nurse = self.nurses[nurse_idx]
            panels[nurse.id].append(p.id)
        for n in self.nurses:
            n.assigned_patients = panels.get(n.id, [])

    def run(self):
        # Initialize patients
        for _ in range(N_INITIAL_PATIENTS):
            self.add_patient(0)
        # Build initial nurse panels
        self.assign_nurse_panels()

        # Main simulation loop
        for t in range(TOTAL_MINUTES):
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
                if patient.seen == 0:
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
                        # If maintain=0, apply linear decay
                        if patient.maintain == 0:
                            patient.severity = max(PATIENT_SEVERITY_MIN, patient.severity - DECAY_PER_MIN)
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
                        from config import MIN_TREATMENT_TIME, MAX_TREATMENT_MULTIPLIER
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
                                    break
                            patient.seen = 0
                            patient.assigned_staff = None
                        continue  # Skip further processing for this patient

    def get_waiting_time_report(self):
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
