"""
Track and visualize how a patient's severity changes over time during simulation.
"""

import random
import numpy as np
import matplotlib.pyplot as plt
from config import *
from patient import Patient
from staff import initialize_staff


class PatientTrackingSimulation:
    def __init__(self, patient_to_track=1):
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
        
        # Tracking data for the specific patient
        self.patient_to_track = f"patient_{patient_to_track}"
        self.tracked_severity = []
        self.tracked_time = []
        self.tracked_status = []  # 'waiting' or 'being_seen'
        self.tracked_staff = []

    def add_patient(self, admit_time):
        if sum(1 for p in self.patients if p.discharge_time is None) >= BEDS:
            return None  # No bed available
        patient = Patient(f"patient_{self.next_patient_id}", admit_time)
        self.patients.append(patient)
        self.next_patient_id += 1
        return patient

    def assign_nurse_panels(self):
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

    def track_patient_state(self, patient):
        """Record the current state of the tracked patient."""
        self.tracked_time.append(self.time / MINUTES_PER_DAY)  # Convert to days
        self.tracked_severity.append(patient.severity)
        self.tracked_status.append('being_seen' if patient.seen == 1 else 'waiting')
        self.tracked_staff.append(patient.assigned_staff if patient.seen == 1 else None)

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
                    self.assign_nurse_panels()
                self.influx_times.pop(0)

            # Every 12 hours, upgrade 10% of <50 severity patients multiplicatively by 10%
            if t > 0 and t % PATIENT_SEVERITY_UPGRADE_INTERVAL == 0:
                lt50 = [p for p in self.patients if p.severity < 50 and p.discharge_time is None]
                n_upgrade = max(1, int(PATIENT_SEVERITY_UPGRADE_PERCENT * len(lt50)))
                upgrade_patients = random.sample(lt50, n_upgrade) if lt50 and n_upgrade > 0 else []
                for p in upgrade_patients:
                    p.severity = min(PATIENT_SEVERITY_MAX, max(PATIENT_SEVERITY_MIN, round(p.severity * PATIENT_SEVERITY_UPGRADE_FACTOR, 2)))

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
                        if patient.maintain is not None and patient.treatment_minutes_left == 0:
                            patient.severity = min(PATIENT_SEVERITY_MAX, patient.severity + 0.5)
                            patient.maintain = None

            # Accumulate waiting time and apply time growth
            # Per config: TIME_GROWTH = "0.5 * t + severity_i" means +0.5 per minute when waiting
            for patient in active_patients:
                if patient.seen == 0:
                    patient.waiting_time += 1
                    patient.start_waiting()
                    # Apply time growth: severity increases by 0.5 per minute when waiting
                    patient.severity = min(PATIENT_SEVERITY_MAX, patient.severity + 0.5)

            # Sort by severity descending
            active_patients.sort(key=lambda p: p.severity, reverse=True)

            # Process each patient
            for patient in active_patients:
                if patient.seen == 1:
                    patient.stop_waiting()
                    if patient.treatment_minutes_left > 0:
                        patient.treatment_minutes_left -= 1
                        if patient.maintain == 0:
                            patient.severity = max(PATIENT_SEVERITY_MIN, patient.severity - 0.5)
                    else:
                        pass
                else:
                    assigned = False
                    for staff in self.providers + self.nurses:
                        if not staff.available:
                            continue
                        if staff.type == 'nurse' and patient.id not in getattr(staff, 'assigned_patients', []):
                            continue
                        staff.available = False
                        staff.current_patient = patient.id
                        patient.seen = 1
                        patient.assigned_staff = staff.id
                        if patient.first_seen_time is None:
                            patient.first_seen_time = t
                            if patient.admit_time > 0:
                                # Assign discharge window for new patients when first seen
                                days = random.randint(*INPATIENT_DAYS_GE50) if patient.severity >= 50 else random.randint(*INPATIENT_DAYS_LT50)
                                patient.time_in_inpatient = days
                        prob = PROVIDER_MAINTAIN_PROB_GE50 if patient.severity >= 50 else PROVIDER_MAINTAIN_PROB_LT50
                        patient.maintain = 1 if random.random() < prob else 0
                        if staff.type == 'provider':
                            mean_minutes = 2 * patient.severity
                        else:
                            mean_minutes = patient.severity
                        patient.treatment_minutes_left = int(np.random.normal(loc=mean_minutes, scale=1))
                        patient.treatment_minutes_left = max(1, patient.treatment_minutes_left)
                        assigned = True
                        patient.stop_waiting()
                        break
                    # If not assigned, severity has already grown in the waiting accumulation loop above

                # Update patient time in hospital first
                patient.total_time_in_hospital += 1

                # Discharge logic - check if patient has reached their discharge window
                # Only discharge if they have a discharge window assigned
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
                        # Track one final time at discharge
                        if patient.id == self.patient_to_track:
                            self.track_patient_state(patient)
                        continue  # Skip further processing for this patient

                # Track our specific patient every hour (every 60 minutes)
                if patient.id == self.patient_to_track and t % 60 == 0:
                    self.track_patient_state(patient)

    def plot_severity_trajectory(self):
        """Create a visualization of the tracked patient's severity over time."""
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
        
        # Plot 1: Severity over time with color coding for status
        colors = ['red' if status == 'waiting' else 'green' for status in self.tracked_status]
        ax1.scatter(self.tracked_time, self.tracked_severity, c=colors, s=50, alpha=0.6)
        ax1.plot(self.tracked_time, self.tracked_severity, 'b-', alpha=0.3, linewidth=1)
        ax1.set_xlabel('Time (days)', fontsize=12)
        ax1.set_ylabel('Severity', fontsize=12)
        ax1.set_title(f'Severity Trajectory for {self.patient_to_track}\n(Red=Waiting, Green=Being Seen)', fontsize=14)
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: Status timeline (waiting vs being seen)
        status_numeric = [1 if status == 'being_seen' else 0 for status in self.tracked_status]
        ax2.fill_between(self.tracked_time, 0, status_numeric, alpha=0.5, color='green', label='Being Seen')
        ax2.fill_between(self.tracked_time, status_numeric, 1, alpha=0.5, color='red', label='Waiting')
        ax2.set_xlabel('Time (days)', fontsize=12)
        ax2.set_ylabel('Patient Status', fontsize=12)
        ax2.set_title('Patient Status Over Time', fontsize=14)
        ax2.set_yticks([0, 1])
        ax2.set_yticklabels(['Waiting', 'Being Seen'])
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('patient_severity_trajectory.png', dpi=150)
        print(f'Severity trajectory plot saved as patient_severity_trajectory.png')
        plt.show()
        
        # Print summary statistics
        patient = next((p for p in self.patients if p.id == self.patient_to_track), None)
        if patient:
            print(f"\n{'='*60}")
            print(f"PATIENT TRAJECTORY SUMMARY: {self.patient_to_track}")
            print(f"{'='*60}")
            print(f"Initial Severity: {self.tracked_severity[0]:.1f}")
            print(f"Final Severity: {self.tracked_severity[-1]:.1f}")
            print(f"Severity Change: {self.tracked_severity[-1] - self.tracked_severity[0]:.1f}")
            print(f"Maximum Severity: {max(self.tracked_severity):.1f}")
            print(f"Minimum Severity: {min(self.tracked_severity):.1f}")
            print(f"Total Time in Hospital: {patient.total_time_in_hospital / MINUTES_PER_DAY:.2f} days")
            print(f"Total Waiting Time: {patient.waiting_time / MINUTES_PER_DAY:.2f} days ({patient.waiting_time} minutes)")
            print(f"Number of Waiting Periods: {len(patient.waiting_periods)}")
            avg_wait = sum(patient.waiting_periods) / len(patient.waiting_periods) if patient.waiting_periods else 0
            print(f"Average Waiting Period: {avg_wait:.1f} minutes")
            print(f"{'='*60}\n")


if __name__ == "__main__":
    print("Enter the patient number to track (default is 1):")
    try:
        patient_num = int(input("Patient number: ") or "1")
    except:
        patient_num = 1
    
    print(f"\nTracking patient_{patient_num}...")
    sim = PatientTrackingSimulation(patient_to_track=patient_num)
    sim.run()
    sim.plot_severity_trajectory()
