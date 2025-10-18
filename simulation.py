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
        self.influx_times = sorted(random.sample(range(1, TOTAL_MINUTES), self.influx_patients_to_add))
        self.waiting_times = {}

    def add_patient(self, admit_time):
        patient = Patient(f"patient_{self.next_patient_id}", admit_time)
        self.patients.append(patient)
        self.next_patient_id += 1
        return patient
    
    def assign_nurses_to_patients(self):
        """Randomly assign 4 patients to each nurse at the start"""
        active_patients = [p for p in self.patients if p.discharge_time is None]
        random.shuffle(active_patients)
        
        for i, nurse in enumerate(self.nurses):
            start_idx = i * 4
            end_idx = min(start_idx + 4, len(active_patients))
            nurse.assigned_patients = [p.id for p in active_patients[start_idx:end_idx]]

    def run(self):
        # Initialize patients
        for _ in range(N_INITIAL_PATIENTS):
            self.add_patient(0)
        
        # Assign nurses to patients (each nurse gets 4 patients)
        self.assign_nurses_to_patients()

        # Main simulation loop
        for t in range(TOTAL_MINUTES):
            self.time = t

            # Add influx patients at random times
            if self.influx_times and t == self.influx_times[0]:
                self.add_patient(t)
                self.influx_times.pop(0)

            # Every 12 hours, upgrade 10% of <50 severity patients to >50
            if t > 0 and t % PATIENT_SEVERITY_UPGRADE_INTERVAL == 0:
                lt50 = [p for p in self.patients if p.severity < 50 and p.discharge_time is None]
                n_upgrade = max(1, int(PATIENT_SEVERITY_UPGRADE_PERCENT * len(lt50)))
                upgrade_patients = random.sample(lt50, n_upgrade) if lt50 and n_upgrade > 0 else []
                for p in upgrade_patients:
                    p.severity = random.randint(51, PATIENT_SEVERITY_MAX)

            # Remove discharged patients from assignment consideration
            active_patients = [p for p in self.patients if p.discharge_time is None]

            # Free up staff who finished treatment
            for staff in self.providers + self.nurses:
                if staff.current_patient is not None:
                    patient = next((p for p in self.patients if p.id == staff.current_patient), None)
                    if patient and patient.treatment_minutes_left <= 0:
                        staff.available = True
                        staff.current_patient = None
                        patient.seen = 0
                        patient.assigned_staff = None
                        # If treatment just ended, add 0.5 to severity
                        if patient.maintain is not None and patient.treatment_minutes_left == 0:
                            patient.severity = min(PATIENT_SEVERITY_MAX, patient.severity + 0.5)
                            patient.maintain = None
                        # Enforce cooldown: patient must wait before being seen again
                        # Higher severity = shorter cooldown (1-5 minutes based on severity)
                        if patient.severity >= 80:
                            patient.cooldown = 1
                        elif patient.severity >= 60:
                            patient.cooldown = 2
                        elif patient.severity >= 40:
                            patient.cooldown = 3
                        else:
                            patient.cooldown = 5

            # Process cooldowns for all active patients
            for patient in active_patients:
                if hasattr(patient, 'cooldown') and patient.cooldown > 0:
                    patient.cooldown -= 1
                    # Only track waiting if not currently being seen AND cooldown just finished
                    if patient.seen == 0 and patient.cooldown == 0:
                        # Cooldown just ended, patient can now be seen
                        pass

            # Sort by severity descending (prioritize high severity)
            active_patients.sort(key=lambda p: p.severity, reverse=True)

            # For each patient, process logic
            for patient in active_patients:
                # Skip if still in cooldown
                if hasattr(patient, 'cooldown') and patient.cooldown > 0:
                    # Patient is in cooldown waiting period
                    if patient.seen == 0:
                        patient.waiting_time += 1
                        patient.start_waiting()
                    continue
                # If patient is already assigned to staff
                if patient.seen == 1:
                    # If just started being seen, stop waiting period
                    patient.stop_waiting()
                    # Continue treatment
                    if patient.treatment_minutes_left > 0:
                        patient.treatment_minutes_left -= 1
                        # If maintain=0, subtract 0.5 from severity
                        if patient.maintain == 0:
                            patient.severity = max(PATIENT_SEVERITY_MIN, patient.severity - 0.5)
                        # If maintain=1, severity stays the same
                        # If treatment ends now, will be freed next loop
                    else:
                        # Treatment just ended, will be freed above
                        pass
                else:
                    # Not seen - try to assign staff
                    assigned = False
                    
                    # Try providers first (they can see any patient)
                    for staff in self.providers:
                        if staff.available:
                            staff.available = False
                            staff.current_patient = patient.id
                            patient.seen = 1
                            patient.assigned_staff = staff.id
                            prob = PROVIDER_MAINTAIN_PROB_GE50 if patient.severity >= 50 else PROVIDER_MAINTAIN_PROB_LT50
                            patient.maintain = 1 if random.random() < prob else 0
                            patient.treatment_minutes_left = int(np.random.normal(loc=2*patient.severity, scale=1))
                            patient.treatment_minutes_left = max(1, patient.treatment_minutes_left)
                            assigned = True
                            patient.stop_waiting()
                            break
                    
                    # If no provider available, check if assigned nurse is available
                    if not assigned:
                        for nurse in self.nurses:
                            if patient.id in nurse.assigned_patients and nurse.available:
                                nurse.available = False
                                nurse.current_patient = patient.id
                                patient.seen = 1
                                patient.assigned_staff = nurse.id
                                prob = PROVIDER_MAINTAIN_PROB_GE50 if patient.severity >= 50 else PROVIDER_MAINTAIN_PROB_LT50
                                patient.maintain = 1 if random.random() < prob else 0
                                patient.treatment_minutes_left = int(np.random.normal(loc=patient.severity, scale=1))
                                patient.treatment_minutes_left = max(1, patient.treatment_minutes_left)
                                assigned = True
                                patient.stop_waiting()
                                break
                    
                    if not assigned:
                        # No staff available, add 0.5 to severity
                        patient.severity = min(PATIENT_SEVERITY_MAX, patient.severity + 0.5)
                        patient.waiting_time += 1
                        patient.start_waiting()

                # Update patient time in hospital
                patient.remaining_minutes -= 1
                patient.total_time_in_hospital += 1

                # Discharge logic
                if patient.severity >= 50 and (t - patient.admit_time) >= DISCHARGE_MINUTES_GE50:
                    patient.discharge_time = t
                    patient.discharge_reason = 'forced_ge50'
                elif patient.severity < 50 and (t - patient.admit_time) >= DISCHARGE_MINUTES_LT50:
                    patient.discharge_time = t
                    patient.discharge_reason = 'forced_lt50'
                elif patient.remaining_minutes <= 0:
                    patient.discharge_time = t
                    patient.discharge_reason = 'natural'

    def get_waiting_time_report(self):
        report = []
        for patient in self.patients:
            if patient.discharge_time is not None:
                avg_wait = (sum(patient.waiting_periods) / len(patient.waiting_periods)) if patient.waiting_periods else 0
                report.append({
                    'patient_id': patient.id,
                    'initial_severity': getattr(patient, 'initial_severity', patient.severity),
                    'waiting_time_minutes': patient.waiting_time,
                    'waiting_time_days': patient.waiting_time / MINUTES_PER_DAY,
                    'average_waiting_period_minutes': avg_wait,
                    'average_waiting_period_days': avg_wait / MINUTES_PER_DAY if avg_wait else 0,
                    'waiting_periods': patient.waiting_periods
                })
        return report
