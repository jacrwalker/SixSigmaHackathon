"""
Configuration for the custom hospital simulation (fresh branch rewrite)
"""

import random
import numpy as np

# Time parameters
MINUTES_PER_DAY = 1440
SIM_DAYS = 28
TOTAL_MINUTES = SIM_DAYS * MINUTES_PER_DAY

# Patient parameters
N_INITIAL_PATIENTS = 20
PATIENT_SEVERITY_MIN = 1
PATIENT_SEVERITY_MAX = 100
INPATIENT_DAYS_GE50 = (1, 7)  # inclusive
INPATIENT_DAYS_LT50 = (1, 4)  # inclusive
DISCHARGE_MINUTES_GE50 = 8 * MINUTES_PER_DAY
DISCHARGE_MINUTES_LT50 = 5 * MINUTES_PER_DAY
PATIENT_INFLUX_RATE = 0.2  # 20% influx over simulation
PATIENT_INFLUX_TOTAL = int(N_INITIAL_PATIENTS * PATIENT_INFLUX_RATE)
PATIENT_SEVERITY_UPGRADE_INTERVAL = 12 * 60  # every 12 hours
PATIENT_SEVERITY_UPGRADE_PERCENT = 0.1  # 10% of <50 patients

# Staff parameters
N_PROVIDERS = 1
N_NURSES = 5

# Treatment parameters
PROVIDER_MAINTAIN_PROB_GE50 = 0.10
PROVIDER_MAINTAIN_PROB_LT50 = 0.01

# Output
OUTPUT_CSV = "waiting_times_new_system.csv"

# Random seed for reproducibility
RANDOM_SEED = 42
def initialize_random_seeds():
    random.seed(RANDOM_SEED)
    np.random.seed(RANDOM_SEED)
