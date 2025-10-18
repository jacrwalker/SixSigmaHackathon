import random
from config import (
    PATIENT_SEVERITY_MIN, PATIENT_SEVERITY_MAX,
    INPATIENT_DAYS_GE50, INPATIENT_DAYS_LT50, MINUTES_PER_DAY
)

class Patient:
    def __init__(self, pid, admit_time):
        self.id = pid
        self.severity = random.randint(PATIENT_SEVERITY_MIN, PATIENT_SEVERITY_MAX)
        self.initial_severity = self.severity  # Store initial severity
        self.admit_time = admit_time
        self.time_in_inpatient = (
            random.randint(*INPATIENT_DAYS_GE50) if self.severity >= 50 else random.randint(*INPATIENT_DAYS_LT50)
        )
        self.remaining_minutes = self.time_in_inpatient * MINUTES_PER_DAY
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
        self.cooldown = 10  # Minimum waiting period (in minutes) after each treatment

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
            'time_in_inpatient': self.time_in_inpatient,
            'remaining_minutes': self.remaining_minutes,
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
