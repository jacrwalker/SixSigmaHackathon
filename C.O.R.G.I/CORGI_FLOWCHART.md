# C.O.R.G.I Hospital Simulation - System Architecture & Flow

## 📊 High-Level System Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         MAIN.PY                                 │
│                    (Entry Point)                                │
│  • Initializes Simulation                                       │
│  • Runs the simulation                                          │
│  • Exports results to CSV                                       │
│  • Displays summary report                                      │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ├─────────────────────┐
                     │                     │
                     ▼                     ▼
        ┌────────────────────┐   ┌────────────────────┐
        │    CONFIG.PY       │   │  SIMULATION.PY     │
        │  (Parameters)      │◄──┤   (Core Logic)     │
        │                    │   │                    │
        │ • Time settings    │   │ • Main loop        │
        │ • Patient params   │   │ • Patient flow     │
        │ • Staff params     │   │ • Staff assignment │
        │ • Treatment rules  │   │ • Discharge logic  │
        │ • Random seed      │   │ • Severity updates │
        └────────────────────┘   └───────┬────────────┘
                                         │
                     ┌───────────────────┼──────────────────┐
                     │                   │                  │
                     ▼                   ▼                  ▼
        ┌────────────────────┐ ┌────────────────┐ ┌───────────────┐
        │    PATIENT.PY      │ │   STAFF.PY     │ │  OUTPUT CSV   │
        │   (Patient Class)  │ │ (Staff Classes)│ │               │
        │                    │ │                │ │ • patient_id  │
        │ • ID & severity    │ │ • Providers    │ │ • severities  │
        │ • Waiting tracking │ │ • Nurses       │ │ • waiting     │
        │ • Treatment state  │ │ • Availability │ │ • treatment   │
        └────────────────────┘ └────────────────┘ └───────────────┘
```

---

## 🔄 Detailed Simulation Flow

### **Phase 1: Initialization**

```
START (main.py)
   │
   ├─► Create Simulation() object
   │      │
   │      ├─► Load config.py parameters
   │      │     • BEDS = 20
   │      │     • N_INITIAL_PATIENTS = 18
   │      │     • N_PROVIDERS = 3
   │      │     • N_NURSES = 5
   │      │     • SIM_DAYS = 28
   │      │     • RANDOM_SEED = 52152
   │      │
   │      ├─► Initialize random seed (config.initialize_random_seeds())
   │      │
   │      ├─► Initialize staff (staff.py)
   │      │     • Create 3 Provider objects
   │      │     • Create 5 Nurse objects
   │      │
   │      ├─► Create 18 initial patients (patient.py)
   │      │     • Each Patient gets random severity (1-100)
   │      │     • Store initial_severity
   │      │     • Assign discharge window based on severity
   │      │
   │      └─► Assign nurse panels
   │            • Patients 1-4 → Nurse 1
   │            • Patients 5-8 → Nurse 2
   │            • Patients 9-12 → Nurse 3
   │            • Patients 13-16 → Nurse 4
   │            • Patients 17-18 → Nurse 5
   │
   └─► simulation.run()
```

---

### **Phase 2: Main Simulation Loop (28 days = 40,320 minutes)**

```
FOR EACH MINUTE (t = 0 to 40,319):
   │
   ├─► PATIENT INFLUX
   │     │
   │     └─► If influx scheduled at minute t AND beds available:
   │           • Create new Patient(admit_time=t)
   │           • Initial severity: random 1-100
   │           • No discharge window yet (assigned after first treatment)
   │           • Reassign nurse panels to include new patient
   │
   ├─► RANDOM SEVERITY UPGRADE (every 12 hours)
   │     │
   │     └─► If t % (12*60) == 0:
   │           • Find 10% of patients with severity < 50
   │           • Increase their severity by 10% (multiplicative)
   │           • Cap at 100
   │
   ├─► FREE STAFF FROM COMPLETED TREATMENTS
   │     │
   │     └─► For each Provider/Nurse:
   │           │
   │           └─► If current_patient exists AND treatment_minutes_left == 0:
   │                 • Apply end-of-session bump (+0.5 to severity)
   │                 • Mark staff as available
   │                 • Mark patient as not seen (seen=0)
   │                 • If nurse freed, immediately reassign to next waiting patient
   │
   ├─► ACCUMULATE WAITING TIME
   │     │
   │     └─► For each active patient not being seen:
   │           • waiting_time += 1 minute
   │           • patient.start_waiting() (track period)
   │           • Severity += GROWTH_PER_MIN (0.5)
   │           • Cap severity at 100
   │
   ├─► PRIORITIZE & ASSIGN STAFF
   │     │
   │     ├─► Sort patients by severity (highest first)
   │     │
   │     └─► For each patient (in severity order):
   │           │
   │           ├─► If patient is BEING SEEN (seen=1):
   │           │     • treatment_minutes_left -= 1
   │           │     • total_treatment_time += 1
   │           │     • If maintain=0: severity -= DECAY_PER_MIN
   │           │     • If maintain=1: severity stays same
   │           │     • patient.stop_waiting()
   │           │
   │           └─► If patient is WAITING (seen=0):
   │                 │
   │                 └─► Try to assign staff:
   │                       │
   │                       ├─► Check Providers (any patient)
   │                       │     • If available → assign
   │                       │
   │                       └─► Check Nurses (panel constraint)
   │                             • Only if patient in nurse's panel
   │                             • If available → assign
   │                       
   │                       If assigned:
   │                         • Set patient.seen = 1
   │                         • Set staff.available = False
   │                         • Calculate maintain probability
   │                         • Set treatment_minutes_left
   │                         • If first time seen: assign discharge window
   │                         • patient.stop_waiting()
   │
   └─► DISCHARGE LOGIC
         │
         └─► For each patient:
               │
               └─► If time_in_hospital >= discharge_window:
                     • Set discharge_time = t
                     • Set discharge_reason = 'natural'
                     • patient.stop_waiting()
                     • Free assigned staff
                     • If nurse freed, reassign to next waiting patient

NEXT MINUTE
```

---

### **Phase 3: Data Export & Reporting**

```
simulation.run() COMPLETE
   │
   ├─► simulation.get_waiting_time_report()
   │     │
   │     └─► For each discharged patient:
   │           • Extract patient_id
   │           • Extract initial_severity
   │           • Extract final_severity
   │           • Calculate waiting_time_minutes (total)
   │           • Calculate average_waiting_period_minutes
   │           • Count n_waiting_periods
   │           • Store treatment_time_minutes
   │           • Convert to days
   │           │
   │           └─► Return list of dictionaries
   │
   ├─► Convert to Pandas DataFrame
   │
   ├─► Export to CSV (scratch_waiting_times_system.csv)
   │
   └─► Display summary (head 20 rows)
         • patient_id
         • initial_severity
         • final_severity
         • waiting_time_minutes
         • average_waiting_period_minutes
         • n_waiting_periods

END
```

---

## 🔗 File Interdependencies

### **1. main.py → ALL FILES**
- **Imports:** `Simulation` from `simulation.py`, `OUTPUT_CSV` from `config.py`
- **Purpose:** Orchestrates the entire simulation workflow
- **Outputs:** CSV file with patient data

### **2. config.py → STANDALONE**
- **No imports** (except `random` and `numpy`)
- **Purpose:** Single source of truth for all parameters
- **Used by:** All other files

### **3. simulation.py → USES ALL**
- **Imports:** 
  - `config.py`: All parameters (`BEDS`, `GROWTH_PER_MIN`, etc.)
  - `patient.py`: `Patient` class
  - `staff.py`: `initialize_staff()` function
- **Purpose:** Core simulation engine
- **Key Methods:**
  - `__init__()`: Setup
  - `run()`: Main loop (40,320 iterations)
  - `add_patient()`: Patient admission
  - `assign_nurse_panels()`: Nurse-patient mapping
  - `get_waiting_time_report()`: Data extraction

### **4. patient.py → USES CONFIG**
- **Imports:** Parameters from `config.py`
- **Purpose:** Patient state management
- **Key Methods:**
  - `__init__()`: Create patient with random severity
  - `start_waiting()`: Begin tracking wait period
  - `stop_waiting()`: End wait period, append to list
  - `to_dict()`: Export patient data

### **5. staff.py → USES CONFIG**
- **Imports:** `N_PROVIDERS`, `N_NURSES` from `config.py`
- **Purpose:** Staff object creation
- **Classes:**
  - `Provider`: Doctor/practitioner (no panel constraint)
  - `Nurse`: Nurse with assigned patient panel
- **Function:** `initialize_staff()` returns lists of staff objects

---

## 📈 Key Data Flows

### **Severity Dynamics**
```
Initial Severity (admission)
   │
   ├─► WAITING: +0.5/min (GROWTH_PER_MIN)
   │
   ├─► TREATMENT: -0.5/min (DECAY_PER_MIN) if maintain=0
   │                 0/min if maintain=1
   │
   ├─► RANDOM UPGRADE: ×1.10 every 12 hours (10% of <50 patients)
   │
   └─► Final Severity (discharge)
```

### **Waiting Time Tracking**
```
Patient Admitted
   │
   ├─► Waiting Period 1
   │     • start_waiting() → counter increments
   │     • Staff assigned → stop_waiting() → append to list
   │
   ├─► Treatment Session
   │     • No waiting accumulation
   │
   ├─► Waiting Period 2
   │     • start_waiting() → counter increments
   │     • Staff assigned → stop_waiting() → append to list
   │
   └─► Discharge
         • Final stop_waiting()
         • Calculate average: sum(periods) / len(periods)
```

### **Staff Assignment Logic**
```
Patient needs treatment (seen=0, severity calculated)
   │
   ├─► Sort all patients by severity (descending)
   │
   ├─► For highest-severity patient:
   │     │
   │     ├─► Try Providers first (any patient)
   │     │     • Provider available? → Assign
   │     │
   │     └─► Try Nurses (panel constraint)
   │           • Is patient in nurse's panel?
   │           • Nurse available? → Assign
   │
   └─► If no staff available: continue waiting (+0.5 severity/min)
```

---

## 📁 Output CSV Structure

| Column | Source | Calculation |
|--------|--------|-------------|
| `patient_id` | `patient.id` | Auto-generated string |
| `initial_severity` | `patient.initial_severity` | Set at admission (1-100) |
| `final_severity` | `patient.severity` | Dynamic, updated every minute |
| `waiting_time_minutes` | `patient.waiting_time` | Incremented each minute while waiting |
| `waiting_time_days` | `waiting_time_minutes / 1440` | Conversion |
| `treatment_time_minutes` | `patient.total_treatment_time` | Incremented each minute in treatment |
| `treatment_time_days` | `treatment_time_minutes / 1440` | Conversion |
| `average_waiting_period_minutes` | `sum(patient.waiting_periods) / len(...)` | Mean of all wait periods |
| `average_waiting_period_days` | `average_waiting_period_minutes / 1440` | Conversion |
| `n_waiting_periods` | `len(patient.waiting_periods)` | Count of distinct wait periods |
| `waiting_periods` | `patient.waiting_periods` | List of all period lengths |

---

## 🎯 Summary

The C.O.R.G.I system simulates a 28-day hospital operation with:

✅ **5 interconnected Python files** working together  
✅ **Minute-by-minute simulation** (40,320 time steps)  
✅ **Dynamic severity model** (growth while waiting, decay during treatment)  
✅ **Realistic constraints** (20 beds, 3 providers, 5 nurses with panels)  
✅ **Detailed waiting time tracking** (multiple periods per patient)  
✅ **Comprehensive CSV output** for analysis  

The flow is: **main.py orchestrates** → **simulation.py executes** → **patient.py & staff.py manage state** → **config.py provides rules** → **CSV stores results**
