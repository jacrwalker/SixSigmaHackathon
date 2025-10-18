"""
Configuration for the custom hospital simulation (fresh branch rewrite)

This file defines the rules of the system. The simulator should faithfully
implement these parameters: bed capacity, staffing, patient influx,
severity dynamics, discharge windows, and the output spec.
"""

import random
import numpy as np

# Time parameters
MINUTES_PER_DAY = 1440
SIM_DAYS = 28
TOTAL_MINUTES = SIM_DAYS * MINUTES_PER_DAY


# Patient parameters
#----Beds and Staffing----
# 20 Beds total, starting with 18 patients, 3 providers (doctors/practitioners), 5 nurses
# Bed capacity is hard-capped: at most 20 patients in the system at any time.
BEDS = 20
#---Nurse Assignment----
# Nurses can handle up to 4 patients each - patients assigned to nurses by ID order
# patients assigned to nurses by ID order - grouped consecutively (ex patients 1-4 go to nurse 1, 5-8 to nurse 2, etc)
#----Patient Characteristics and Flow----
# Initial patients have severity 1-100 randomly assigned
# 1 patient influx every 12 hours (randomly timed within each 12-hour block)
# Patients admitted at time 0 (initial cohort) have a random discharge window based on initial severity.
# New patients are discharged randomly after being seen:
#   - if severity < 50: min 3 days, max 7 days (federal regulation)
#   - if severity >= 50: min 3 days, max 28 days
# Max amount of patients in system at any time is 20 (beds)


N_INITIAL_PATIENTS = 18
PATIENT_SEVERITY_MIN = 1
PATIENT_SEVERITY_MAX = 100

PATIENT_INFLUX_RATE = (1 / (SIM_DAYS * 2))  # 1 patient every 12 hours (not directly used; for documentation)
PATIENT_INFLUX_TOTAL = SIM_DAYS * 2  # Total of 56 influx patients over 28 days, one per 12-hour block

# Inpatient day ranges by initial/current severity
# Used for selecting a random discharge window (in days)
INPATIENT_DAYS_LT50 = (3, 7)
INPATIENT_DAYS_GE50 = (3, 28)



# Staff parameters
# 20 Beds total, starting with 18 patients, 3 providers (doctors/practitioners), 5 nurses
N_PROVIDERS = 3
N_NURSES = 5
NURSES_MAX_PATIENTS = 4  # Assigned panel size per nurse (bed-slot groups of 4)

# Treatment parameters
# Time Growth function (while patient is not being seen)
TIME_GROWTH = "0.5 * t + severity_i"
# Time Decay function (while patient is being seen)
TIME_DECAY = "-0.5 * t + severity_i"
# (Maintain function) Probability of provider maintaining treatment based on severity
PROVIDER_MAINTAIN_PROB_GE50 = 0.10
PROVIDER_MAINTAIN_PROB_LT50 = 0.01

# Random Effect
# Every 12 hours, 10% of patients with severity < 50 have their severity increased by 10% (multiplicative), capped at 100
PATIENT_SEVERITY_UPGRADE_INTERVAL = 12 * 60  # every 12 hours
PATIENT_SEVERITY_UPGRADE_PERCENT = 0.10  # 10% of <50 patients selected
PATIENT_SEVERITY_UPGRADE_FACTOR = 1.10  # increase current severity by 10%

# Output
# What goes in the csv
# Patient clock starts at 0 when they are admitted
# If patient is seen then clock time is logged; clock timer restarts when patient is waiting again
# if patient is not seen, waiting clock time continues to accumulate
# So we note how many waiting times there are, and the lengths of each waiting period in a vector
# Take an average waiting period length for each patient into a list/vector 

# Save the severity at admission time as initial_severity
# Log the severity at the same time when clock timer is logged

# for each patient, log: current severity, which was the initial severity + 0.5 for total clock time they were waiting - 0.5 total clock time they were being seen
# organize display such that patients with highest current severity are shown first



OUTPUT_CSV = "scratch_waiting_times_system.csv"

# Random seed for reproducibility
RANDOM_SEED = 42
def initialize_random_seeds():
    random.seed(RANDOM_SEED)
    np.random.seed(RANDOM_SEED)
