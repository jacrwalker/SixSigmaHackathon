# SixSigmaHackathon
SYSEN 5300 
Team Name: Dose of Innovation
Members: Maddie Slavett, Babette Gilles, Jose Aguilar, Fabien de Silva, Jackie Walker

Code C.O.R.G.I. — “Clinical Operations & Response Gap Intelligence”

A real-time dashboard that visualizes patient wait times, and is designed to simulate hospital workflows for testing and analysis. 

Hospitals are incredibly complex systems with numerous moving pieces. In our hospital system, patients are complaining of wide and note wide and irregular gaps between provider and nurse check-ins, leading to woese health outcomes and potentoally longer stays in our inpatient care units. Our goal is to develop a tool to reduce wait times between patients by creating a scale that prioritized patients with the highest severity scores without leaving anyone behind. 

# 🏥 Hospital Simulation Overview

This project simulates the dynamic flow of patients in a small hospital unit over a two-week period, using a minute-by-minute time resolution. It models patient severity, staff interactions (providers and nurses), waiting times, and discharges based on configurable rules.

The simulation is useful for understanding patient throughput, staff utilization, and severity trends over time in a controlled environment.

# 🧠 Core Concept

Each simulated patient has:

A severity rating (1–100)

A stay duration (inpatient days)

A waiting time and treatment time history

A discharge condition (based on time or treatment)

Each provider or nurse can treat one patient at a time, with treatment duration and improvement depending on patient severity.

Patients are dynamically admitted, treated, and discharged according to the simulation rules.

# ⚙️ Simulation Parameters
| Category      | Parameter                                                     | Description                               |
| ------------- | ------------------------------------------------------------- | ----------------------------------------- |
| **Time**      | `SIM_DAYS = 28`                                               | Simulation runs for 28 days               |
|               | `TOTAL_MINUTES = SIM_DAYS * 1440`                             | 1-minute timesteps                        |
| **Patients**  | `BEDS = 20`                                                   | Total bed capacity                        |
|               | `N_INITIAL_PATIENTS = 18`                                     | Initial patients admitted at t=0          |
|               | `PATIENT_SEVERITY_MIN/MAX = 1, 100`                           | Random severity assignment                |
|               | `INPATIENT_DAYS_LT50 = (3, 7)`                                | Discharge window (severity <50)           |
|               | `INPATIENT_DAYS_GE50 = (3, 28)`                               | Discharge window (severity ≥50)           |
|               | `PATIENT_INFLUX_TOTAL = SIM_DAYS * 2`                         | 1 new patient per 12 hours                |
| **Staff**     | `N_PROVIDERS = 3`                                             | Physicians                                |
|               | `N_NURSES = 5`                                                | Nurses                                    |
|               | `NURSES_MAX_PATIENTS = 4`                                     | Nurse panels (groups of patients)         |
| **Treatment** | `GROWTH_PER_MIN = 0.5`                                        | Severity increase per waiting minute      |
|               | `DECAY_PER_MIN = 0.5`                                         | Severity decrease per treatment minute    |
|               | `PROVIDER_MAINTAIN_PROB_GE50 = 0.10`                          | 10% chance of maintaining condition (≥50) |
|               | `PROVIDER_MAINTAIN_PROB_LT50 = 0.01`                          | 1% chance of maintaining condition (<50)  |
| **Upgrades**  | Every 12h, 10% of patients with severity <50 upgraded by +10% |                                           |
| **Output**    | `OUTPUT_CSV = "scratch_waiting_times_system.csv"`             | Logs patient waiting stats                |

# 🩺 Simulation Logic

Initialization

18 patients are admitted.

Each patient is assigned:

    Severity rating (1–100)

    Inpatient duration (based on severity)

    Seen/not-seen status (0 at t=0)

    3 providers and 5 nurses are created and assigned to patient panels.

Minute-by-Minute Loop

Runs for 28 * 1440 minutes.

Each iteration:

    Adds new patients (if beds are available).

    Upgrades severity for 10% of low-severity patients (every 12 hours).

    Updates patient waiting and treatment states.

    Frees staff when treatments end.

    Sorts patients by severity and assigns available staff.

    Discharges patients when their inpatient time expires.

Patient Flow Rules

    Waiting: Severity increases by +0.5/minute.

    Being Seen: Severity decreases by -0.5/minute (or stays constant if “maintained”).

    Discharge: Patients leave after 3–7 days (<50) or 3–28 days (≥50).

Treatment Assignments

  Provider or nurse is randomly assigned if available.

Treatment duration:

    Random between 10 and (severity * 2) minutes.

Maintain chance:

    10% if severity ≥50

    1% if severity <50

Waiting Time Tracking

    The simulation tracks how long each patient waits before being seen.

    Once discharged, their average waiting time and total waiting/treatment times are logged.

# 🧮 Output

After the simulation completes, a CSV file is generated:

scratch_waiting_times_system.csv

| Column                           | Description                          |
| -------------------------------- | ------------------------------------ |
| `patient_id`                     | Unique patient identifier            |
| `initial_severity`               | Severity on admission                |
| `final_severity`                 | Severity at discharge                |
| `waiting_time_minutes`           | Total waiting time                   |
| `waiting_time_days`              | Waiting time (in days)               |
| `average_waiting_period_minutes` | Mean waiting time per event          |
| `n_waiting_periods`              | Number of separate waiting intervals |
| `treatment_time_minutes`         | Total treatment duration             |
