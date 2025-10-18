import random
from config import N_PROVIDERS, N_NURSES, NURSES_MAX_PATIENTS

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
