"""
Configuration parameters for the hospital simulation (NEW SYSTEM)
"""

import numpy as np
import random

# -------------------------
# Time Parameters
# -------------------------
MINUTES_PER_DAY = 1440
SIM_DAYS = 14
TOTAL_MINUTES = SIM_DAYS * MINUTES_PER_DAY

# -------------------------
# Patient Parameters
# -------------------------
MAX_HOSPITAL_BEDS = 25  # Maximum bed capacity
N_INITIAL_PATIENTS = 20
DAILY_ADMITS_MEAN = 2  # Mean for Poisson distribution
MIN_SEVERITY = 1
MAX_SEVERITY = 100

# Forced discharge thresholds based on admission severity
DISCHARGE_LT50_MIN = 4 * MINUTES_PER_DAY  # <50: discharge after 4 days
DISCHARGE_GE50_MIN = 8 * MINUTES_PER_DAY  # ≥50: discharge after 8 days

# -------------------------
# Staff Parameters (Scaled for one hospital section)
# -------------------------
# Doctor parameters (1 doctor to 20 patients)
N_DOCTORS = 1  # For ~25 patients (1:20-25 ratio)
DOCTOR_CAPACITY = 25
DOCTOR_VISIT_TIME = 30  # minutes per visit

# Nurse parameters (1 nurse to 3-4 patients)
N_NURSES = 7  # For ~25 patients (1:3-4 ratio)
NURSE_CAPACITY = 4
NURSE_VISIT_TIME = 30  # minutes per visit

# Staff fatigue and rest
STAFF_FATIGUE_MIN = 0.1
STAFF_FATIGUE_MAX = 0.5
STAFF_FATIGUE_THRESHOLD = 2.0
STAFF_REST_MIN = 10
STAFF_REST_MAX = 30

# -------------------------
# Severity Score Dynamics (Gas Pedal/Meter System)
# -------------------------
# When being seen (maintain=False): decay rate per minute
SEVERITY_DECAY_MULTIPLIER = 0.5  # Decay = -0.5 × initial_severity per minute

# When NOT being seen (waiting): growth rate per minute
SEVERITY_GROWTH_RATE = 0.1  # Severity increases by this amount per minute when waiting

# When being seen (maintain=True): no change
# Severity stays constant during maintenance visits

MAINTAIN_PROBABILITY = 0.2  # Probability of maintenance visit (determined once at assignment)

# -------------------------
# Random Seeds
# -------------------------
RANDOM_SEED = 1

def initialize_random_seeds():
    """Initialize random seeds for reproducibility"""
    np.random.seed(RANDOM_SEED)
    random.seed(RANDOM_SEED)
