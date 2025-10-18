"""
Patient management for the hospital simulation
"""

import numpy as np
from config import MIN_SEVERITY, MAX_SEVERITY, MINUTES_PER_DAY


class PatientManager:
    """Manages patient creation and tracking"""
    
    def __init__(self):
        self.next_patient_id = 1
        self.active_patients = {}
        self.discharged_records = {}
    
    def create_patient(self, admit_minute):
        """Create a new patient with random severity and initial stay estimate"""
        pid = f'patient_{self.next_patient_id}'
        self.next_patient_id += 1
        
        # Random severity between 1-100
        severity = int(np.random.randint(MIN_SEVERITY, MAX_SEVERITY + 1))
        
        # Initial estimated days based on severity
        init_days = np.random.randint(1, 8) if severity >= 50 else np.random.randint(1, 5)
        remaining_time = init_days * MINUTES_PER_DAY
        
        patient = {
            'id': pid,
            'admit_minute': admit_minute,
            'severity': float(severity),
            'admission_severity': float(severity),  # Stored once for discharge threshold
            'initial_days': init_days,
            'remaining_time': remaining_time,
            'seen': 0,
            'assigned_staff_id': None,
            'assigned_visit_total': 0,
            'assigned_visit_remaining': 0,
            'assigned_maintain': None,  # Determined ONCE at first assignment
            'first_assignment_done': False,  # Track if patient has been assigned before
            'total_time_in_hospital': 0,
            'total_wait_time': 0,
            'history': []
        }
        
        self.active_patients[pid] = patient
        return patient
    
    def discharge_patient(self, pid, discharge_minute, reason):
        """Discharge a patient and move to discharged records"""
        if pid not in self.active_patients:
            return None
        
        patient = self.active_patients[pid]
        patient['discharge_minute'] = discharge_minute
        patient['total_time_in_hospital'] = discharge_minute - patient['admit_minute']
        patient['history'].append((discharge_minute, f'discharged_{reason}'))
        
        # Move to discharged records
        self.discharged_records[pid] = patient
        del self.active_patients[pid]
        
        return patient
    
    def update_patient_severity(self, pid, change_amount):
        """Update patient severity with bounds checking"""
        if pid not in self.active_patients:
            return
        
        patient = self.active_patients[pid]
        patient['severity'] += change_amount
        # Cap between MIN_SEVERITY and MAX_SEVERITY
        patient['severity'] = min(max(patient['severity'], MIN_SEVERITY), MAX_SEVERITY)
    
    def get_unassigned_patients(self):
        """Get list of patients not currently assigned to staff"""
        return [p for p in self.active_patients.values() if p['assigned_staff_id'] is None]
    
    def get_patient(self, pid):
        """Get patient by ID"""
        return self.active_patients.get(pid)
    
    def get_all_active_patients(self):
        """Get all active patients"""
        return list(self.active_patients.values())
    
    def get_discharged_patients(self):
        """Get all discharged patients"""
        return list(self.discharged_records.values())
