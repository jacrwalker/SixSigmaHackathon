"""
Staff management for the hospital simulation
"""

import random
from config import (
    DOCTOR_VISIT_TIME, NURSE_VISIT_TIME,
    STAFF_FATIGUE_MIN, STAFF_FATIGUE_MAX,
    STAFF_FATIGUE_THRESHOLD, STAFF_REST_MIN, STAFF_REST_MAX,
    MAINTAIN_PROBABILITY
)


class StaffManager:
    """Manages staff (doctors and nurses) creation and tracking"""
    
    def __init__(self):
        self.next_staff_id = 1
        self.staff_by_id = {}
        self.doctors = []
        self.nurses = []
    
    def create_staff(self, staff_type, capacity, visit_time):
        """Create a new staff member (doctor or nurse)"""
        sid = f'{staff_type}_{self.next_staff_id}'
        self.next_staff_id += 1
        
        staff = {
            'id': sid,
            'type': staff_type,
            'capacity': capacity,
            'visit_time': visit_time,
            'available': True,
            'assigned_patient': None,
            'remaining_visit': 0,
            'maintain': None,
            'fatigue': 0.0,
            'resting': 0
        }
        
        self.staff_by_id[sid] = staff
        
        if staff_type == 'doctor':
            self.doctors.append(sid)
        else:
            self.nurses.append(sid)
        
        return staff
    
    def create_doctors(self, n_doctors):
        """Create multiple doctors"""
        for _ in range(n_doctors):
            self.create_staff('doctor', None, DOCTOR_VISIT_TIME)
    
    def create_nurses(self, n_nurses):
        """Create multiple nurses"""
        for _ in range(n_nurses):
            self.create_staff('nurse', None, NURSE_VISIT_TIME)
    
    def get_available_staff(self):
        """Get list of available staff members"""
        return [s for s in self.staff_by_id.values() if s['available'] and s['resting'] == 0]
    
    def assign_staff_to_patient(self, staff_id, patient_id):
        """Assign a staff member to a patient"""
        if staff_id not in self.staff_by_id:
            return False
        
        staff = self.staff_by_id[staff_id]
        staff['available'] = False
        staff['assigned_patient'] = patient_id
        staff['remaining_visit'] = staff['visit_time']
        staff['maintain'] = random.random() < MAINTAIN_PROBABILITY
        
        return staff['maintain']
    
    def update_staff(self, patient_manager):
        """Update all staff members for one time step"""
        for sid, staff in self.staff_by_id.items():
            # Handle resting staff
            if staff['resting'] > 0:
                staff['resting'] -= 1
                continue
            
            # Handle staff currently visiting patients
            if staff['remaining_visit'] > 0:
                staff['remaining_visit'] -= 1
                
                # Visit completed
                if staff['remaining_visit'] == 0:
                    pid = staff['assigned_patient']
                    patient = patient_manager.get_patient(pid)
                    
                    if patient:
                        patient['seen'] += 1
                        patient['assigned_staff_id'] = None
                    
                    staff['available'] = True
                    staff['assigned_patient'] = None
                    staff['maintain'] = None
                    
                    # Add fatigue
                    staff['fatigue'] += random.uniform(STAFF_FATIGUE_MIN, STAFF_FATIGUE_MAX)
                    
                    # Check if staff needs rest
                    if staff['fatigue'] > STAFF_FATIGUE_THRESHOLD:
                        staff['resting'] = random.randint(STAFF_REST_MIN, STAFF_REST_MAX)
                        staff['fatigue'] = 0.0
            else:
                staff['available'] = True
    
    def free_staff_from_patient(self, patient_id):
        """Free any staff assigned to a specific patient (for discharge)"""
        for staff in self.staff_by_id.values():
            if staff['assigned_patient'] == patient_id:
                staff['available'] = True
                staff['assigned_patient'] = None
                staff['remaining_visit'] = 0
                staff['maintain'] = None
    
    def get_staff(self, staff_id):
        """Get staff member by ID"""
        return self.staff_by_id.get(staff_id)
    
    def get_all_staff(self):
        """Get all staff members"""
        return list(self.staff_by_id.values())
