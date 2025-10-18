"""
Main simulation logic for the hospital (NEW SYSTEM)
"""

import random
import numpy as np
from config import (
    TOTAL_MINUTES, MINUTES_PER_DAY,
    N_INITIAL_PATIENTS, DAILY_ADMITS_MEAN,
    MAX_HOSPITAL_BEDS,
    DISCHARGE_LT50_MIN, DISCHARGE_GE50_MIN,
    SEVERITY_DECAY_MULTIPLIER, SEVERITY_GROWTH_RATE,
    N_DOCTORS, N_NURSES,
    initialize_random_seeds
)
from patient import PatientManager
from staff import StaffManager


class HospitalSimulation:
    """Main hospital simulation class"""
    
    def __init__(self):
        # Initialize random seeds
        initialize_random_seeds()
        
        # Initialize managers
        self.patient_manager = PatientManager()
        self.staff_manager = StaffManager()
        
        # Create staff
        self.staff_manager.create_doctors(N_DOCTORS)
        self.staff_manager.create_nurses(N_NURSES)
        
        # Create initial patients
        for _ in range(N_INITIAL_PATIENTS):
            self.patient_manager.create_patient(0)
        
        self.current_time = 0
        self.rejected_admissions = 0  # Track patients turned away due to capacity
    
    def admit_new_patients(self):
        """Admit new patients based on Poisson distribution (respecting bed capacity)"""
        n_admits = np.random.poisson(DAILY_ADMITS_MEAN)
        
        for _ in range(n_admits):
            # Check if hospital has capacity
            current_patients = len(self.patient_manager.active_patients)
            if current_patients < MAX_HOSPITAL_BEDS:
                self.patient_manager.create_patient(self.current_time)
            else:
                # Track rejected admissions (no bed available)
                self.rejected_admissions += 1
    
    def assign_staff_to_patients(self):
        """Assign available staff to unassigned patients"""
        available_staff = self.staff_manager.get_available_staff()
        unassigned_patients = self.patient_manager.get_unassigned_patients()
        
        for staff in available_staff:
            if not unassigned_patients:
                break
            
            # Get next unassigned patient
            patient = unassigned_patients.pop(0)
            
            # Determine maintain status ONLY on first assignment
            if not patient.get('first_assignment_done', False):
                is_maintain = self.staff_manager.assign_staff_to_patient(
                    staff['id'], patient['id']
                )
                patient['assigned_maintain'] = is_maintain
                patient['first_assignment_done'] = True
                patient['history'].append(
                    (self.current_time, f'FIRST_assignment_{staff["id"]}_maintain={is_maintain}')
                )
            else:
                # Subsequent assignments - use existing maintain value
                self.staff_manager.assign_staff_to_patient(
                    staff['id'], patient['id']
                )
                patient['history'].append(
                    (self.current_time, f'reassignment_{staff["id"]}_maintain={patient["assigned_maintain"]}')
                )
            
            # Update patient record
            patient['assigned_staff_id'] = staff['id']
            patient['assigned_visit_total'] += 1
            patient['assigned_visit_remaining'] = staff['visit_time']
    
    def update_patients(self):
        """Update all patients for one time step"""
        patients_to_discharge = []
        
        for patient in self.patient_manager.get_all_active_patients():
            patient['remaining_time'] -= 1
            patient['total_time_in_hospital'] += 1
            
            # ===== NEW SEVERITY DYNAMICS (Gas Pedal System) =====
            # Check if patient is being seen by staff
            if patient['assigned_staff_id'] is None:
                # NOT being seen - severity INCREASES (waiting)
                patient['total_wait_time'] += 1
                severity_change = SEVERITY_GROWTH_RATE  # Growth per minute
                self.patient_manager.update_patient_severity(patient['id'], severity_change)
            else:
                # BEING seen by staff - check maintain status
                if patient.get('assigned_maintain', False):
                    # Maintain = True: severity stays CONSTANT (no change)
                    pass  # No severity change
                else:
                    # Maintain = False: severity DECREASES (treatment working)
                    # Decay rate = -0.5 × initial_severity per minute
                    decay_rate = -SEVERITY_DECAY_MULTIPLIER * patient['admission_severity']
                    self.patient_manager.update_patient_severity(patient['id'], decay_rate)
            
            # Check for forced discharge based on admission severity
            time_in_hospital = self.current_time - patient['admit_minute']
            threshold = (DISCHARGE_GE50_MIN if patient['admission_severity'] >= 50 
                        else DISCHARGE_LT50_MIN)
            
            if time_in_hospital >= threshold:
                patients_to_discharge.append(
                    (patient['id'], f'admission_threshold_after_{time_in_hospital}_min')
                )
                continue
            
            # Natural discharge if remaining time is up
            if patient['remaining_time'] <= 0:
                patients_to_discharge.append((patient['id'], 'natural'))
        
        # Discharge patients
        for pid, reason in patients_to_discharge:
            self.patient_manager.discharge_patient(pid, self.current_time, reason)
            self.staff_manager.free_staff_from_patient(pid)
    
    def run(self):
        """Run the simulation for TOTAL_MINUTES"""
        for t in range(TOTAL_MINUTES):
            self.current_time = t
            
            # Daily new admissions (at start of each day after day 0)
            if t % MINUTES_PER_DAY == 0 and t > 0:
                self.admit_new_patients()
            
            # Update staff (handle visits, fatigue, rest)
            self.staff_manager.update_staff(self.patient_manager)
            
            # Assign available staff to unassigned patients
            self.assign_staff_to_patients()
            
            # Update patients (severity, discharge checks)
            self.update_patients()
    
    def get_results(self):
        """Get simulation results"""
        discharged = self.patient_manager.get_discharged_patients()
        active = self.patient_manager.get_all_active_patients()
        
        return {
            'discharged_patients': discharged,
            'active_patients': active,
            'total_discharged': len(discharged),
            'total_active': len(active),
            'rejected_admissions': self.rejected_admissions,
            'max_capacity': MAX_HOSPITAL_BEDS
        }
    
    def get_waiting_time_report(self):
        """Generate a report of patient IDs and their waiting times"""
        discharged = self.patient_manager.get_discharged_patients()
        
        report = []
        for patient in discharged:
            report.append({
                'patient_id': patient['id'],
                'waiting_time_minutes': patient['total_wait_time'],
                'waiting_time_days': patient['total_wait_time'] / MINUTES_PER_DAY
            })
        
        return report
