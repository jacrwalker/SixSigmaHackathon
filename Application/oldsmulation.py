import random
import csv
from dataclasses import dataclass, field
from typing import List, Optional
import simpy

# -----------------------
# Configuration constants
# -----------------------
SEED = 42
random.seed(SEED)

MINUTE = 1
HOUR = 60 * MINUTE
DAY = 24 * HOUR

SIM_DAYS = 28                                   # 4 weeks
SIM_TIME = SIM_DAYS * DAY                        # minutes

ARRIVAL_RATE_PER_DAY = 1
MEAN_INTERARRIVAL = (24 * 60) / ARRIVAL_RATE_PER_DAY

BED_CAPACITY = 20
INITIAL_PATIENTS = 20

# Status
CRITICAL = "critical"
NORMAL = "normal"

# Initial remaining LOS (for the 20 already inside at t=0)
INIT_CRIT_LOS_DAYS = (5, 8)   # inclusive
INIT_NORM_LOS_DAYS = (3, 5)   # inclusive

# Daily transition probabilities
P_CRIT_TO_NORM = 0.10
P_NORM_TO_CRIT = 0.05

# -----------------------
# Staffing (realistic)
# -----------------------
NUM_DOCTORS = 2
NUM_NURSES = 5
DOC_DAILY_CAP = 40                 # soft cap
NURSE_DAILY_CAP_RANGE = (25, 40)   # per nurse per day

# -----------------------
# Time Parameters (realistic)
# -----------------------
# Doctor buffers (only when treated by a DOCTOR)
DOC_BUFFER_CRIT_MIN = 0
DOC_BUFFER_CRIT_MAX = 5
DOC_BUFFER_NORM_MIN = 0
DOC_BUFFER_NORM_MAX = 10

# Doctor service times
SERVICE_CRIT_MIN = 15
SERVICE_CRIT_MAX = 45
SERVICE_NORM_MIN = 10
SERVICE_NORM_MAX = 25

# Nurse service times
NURSE_SERVICE_MIN = 10
NURSE_SERVICE_MAX = 20

# Cooldown after any treatment
COOLDOWN = 30  # minutes

# SLA thresholds
NORMAL_SLA_MINUTES = 60  # normal patients fast-tracked after 60 min if never seen

# CSV output
CSV_PATH = "patient_avg_waits.csv"
CSV_LIMIT_PATIENTS = 1000  # Show all patients


# -----------------------
# Data structures
# -----------------------
@dataclass
class Patient:
    pid: int
    admitted_time: int
    status: str                         # "critical" | "normal"
    discharge_time: int                 # absolute env time when they leave
    ever_seen: int = 0                  # 0 at t=0, set to 1 once treated
    waits: List[float] = field(default_factory=list)
    num_visits: int = 0
    last_queue_enter: Optional[int] = None
    in_system: bool = True
    last_seen_day: int = -1             # day index (0-based); -1 means never seen yet

@dataclass
class Provider:
    name: str
    kind: str                           # "doctor" | "nurse"
    daily_capacity: int
    remaining_today: int
    busy: bool = False


# -----------------------
# Simulation model
# -----------------------
class HospitalSim:
    def __init__(self, env: simpy.Environment):
        self.env = env
        self.patients: List[Patient] = []
        self.active_patients: List[Patient] = []     # currently admitted (for bed cap)
        self.next_pid = 0

        # Queues (priority order in dispatcher)
        self.first_visit_queue = simpy.FilterStore(env)  # TOP PRIORITY: any patient never seen
        self.crit_queue = simpy.FilterStore(env)
        self.sla_daily_queue = simpy.FilterStore(env)    # must be seen today (after first visit)
        self.norm_fast_queue = simpy.FilterStore(env)    # normals waiting >= 60 min and never seen
        self.norm_queue = simpy.FilterStore(env)

        # Providers
        self.providers: List[Provider] = []

        # Create doctors
        for i in range(NUM_DOCTORS):
            p = Provider(
                name=f"Doctor-{i+1}",
                kind="doctor",
                daily_capacity=DOC_DAILY_CAP,
                remaining_today=DOC_DAILY_CAP,
            )
            self.providers.append(p)

        # Create nurses
        for i in range(NUM_NURSES):
            daily = random.randint(*NURSE_DAILY_CAP_RANGE)
            p = Provider(
                name=f"Nurse-{i+1}",
                kind="nurse",
                daily_capacity=daily,
                remaining_today=daily,
            )
            self.providers.append(p)

        # Kick off processes
        self.env.process(self.dispatcher())
        self.env.process(self.midnight_resets())
        self.env.process(self.daily_status_flips())
        self.env.process(self.arrival_process())
        self.env.process(self.sla_normal_fasttrack())   # normal never-seen after 60 minutes -> fast lane
        self.env.process(self.daily_sla_promoter())     # not seen today -> daily SLA lane (ALL patients)
        self.env.process(self.first_visit_sweeper())    # ensure all never-seen are in the top-priority queue

        # Seed initial inpatients at t=0
        self.seed_initial_patients()

    # ---------- Patient creation / admission ----------
    def create_patient(self, status: str, los_days: int) -> Optional[Patient]:
        if len(self.active_patients) >= BED_CAPACITY:
            return None  # turned away (no bed)

        pid = self.next_pid
        self.next_pid += 1

        admitted = int(self.env.now)
        discharge_time = admitted + los_days * DAY

        patient = Patient(
            pid=pid,
            admitted_time=admitted,
            status=status,
            discharge_time=discharge_time,
            ever_seen=0,
            last_seen_day=-1,
        )
        self.patients.append(patient)
        self.active_patients.append(patient)

        # Immediately request treatment (enter FIRST-VISIT queue)
        self.env.process(self.patient_cycle(patient))
        return patient

    def seed_initial_patients(self):
        for _ in range(INITIAL_PATIENTS):
            status = NORMAL if random.random() < 0.80 else CRITICAL
            if status == NORMAL:
                los_days = random.randint(*INIT_NORM_LOS_DAYS)
            else:
                los_days = random.randint(*INIT_CRIT_LOS_DAYS)
            self.create_patient(status, los_days)

    # ---------- Arrivals ----------
    def arrival_process(self):
        """Deterministic arrivals: exactly 1 patient every 12 hours (720 minutes)."""
        next_arrival = 12 * HOUR  # first new arrival at t=12h; change to 0 if you want at t=0
        while next_arrival <= SIM_TIME:
            yield self.env.timeout(max(0, next_arrival - self.env.now))

            is_normal = random.random() < 0.80
            status = NORMAL if is_normal else CRITICAL
            if status == NORMAL:
                los_days = random.randint(*INIT_NORM_LOS_DAYS)
            else:
                los_days = random.randint(*INIT_CRIT_LOS_DAYS)

            self.create_patient(status, los_days)
            next_arrival += 12 * HOUR

    # ---------- SLA: normal fast-track after 60 min if never seen ----------
    def sla_normal_fasttrack(self):
        while self.env.now < SIM_TIME:
            items = list(self.norm_queue.items)
            for p in items:
                if (p.in_system and p.status == NORMAL and p.ever_seen == 0 and
                    p.last_queue_enter is not None and
                    (self.env.now - p.last_queue_enter) >= NORMAL_SLA_MINUTES):
                    yield self.norm_queue.get(lambda x, pid=p.pid: x.pid == pid)
                    yield self.norm_fast_queue.put(p)
            yield self.env.timeout(1)

    # ---------- SLA: must be seen once per day (ALL patients) ----------
    def daily_sla_promoter(self):
        """
        Promote ANY patient (critical or normal) who has not been seen today (after their first visit)
        into the daily SLA queue, regardless of their current queue.
        """
        while self.env.now < SIM_TIME:
            current_day = int(self.env.now // DAY)
            # Sweep all patient-holding stores where post-first-visit patients can sit
            for store in (self.crit_queue, self.norm_fast_queue, self.norm_queue):
                items = list(store.items)
                for p in items:
                    if p.in_system and p.ever_seen == 1 and p.last_seen_day < current_day:
                        # Move to SLA queue
                        yield store.get(lambda x, pid=p.pid: x.pid == pid)
                        yield self.sla_daily_queue.put(p)
            yield self.env.timeout(1)

    # ---------- Ensure all never-seen are in top-priority queue ----------
    def first_visit_sweeper(self):
        while self.env.now < SIM_TIME:
            for store in (self.crit_queue, self.sla_daily_queue, self.norm_fast_queue, self.norm_queue):
                items = list(store.items)
                for p in items:
                    if p.in_system and p.ever_seen == 0:
                        yield store.get(lambda x, pid=p.pid: x.pid == pid)
                        yield self.first_visit_queue.put(p)
            yield self.env.timeout(1)

    # ---------- Patient cycle ----------
    def patient_cycle(self, patient: Patient):
        if patient.ever_seen == 0:
            patient.last_queue_enter = int(self.env.now)
            yield self.first_visit_queue.put(patient)

        remaining = max(0, patient.discharge_time - int(self.env.now))
        if remaining > 0:
            yield self.env.timeout(remaining)

    # ---------- Dispatcher ----------
    def dispatcher(self):
        """
        Priority order (FIXED):
          1) first_visit_queue (never seen)  -- overrides capacity caps
          2) sla_daily_queue (must be seen today)  -- now also overrides capacity caps
          3) crit_queue
          4) norm_fast_queue
          5) norm_queue
        """
        while self.env.now < SIM_TIME:
            # Capacity override if there are first-visit OR daily-SLA patients
            override_caps = (len(self.first_visit_queue.items) > 0) or (len(self.sla_daily_queue.items) > 0)

            if override_caps:
                free_providers = [p for p in self.providers if not p.busy]
            else:
                free_providers = [p for p in self.providers if (not p.busy and p.remaining_today > 0)]

            if not free_providers:
                yield self.env.timeout(1)
                continue

            served_someone = False

            for provider in list(free_providers):
                patient = None

                # Priority pick (first_visit -> sla_daily -> critical -> normal_fast -> normal)
                if len(self.first_visit_queue.items) > 0:
                    patient = yield self.first_visit_queue.get(lambda x: True)
                elif len(self.sla_daily_queue.items) > 0:
                    patient = yield self.sla_daily_queue.get(lambda x: True)
                elif len(self.crit_queue.items) > 0:
                    patient = yield self.crit_queue.get(lambda x: True)
                elif len(self.norm_fast_queue.items) > 0:
                    patient = yield self.norm_fast_queue.get(lambda x: True)
                elif len(self.norm_queue.items) > 0:
                    patient = yield self.norm_queue.get(lambda x: True)
                else:
                    continue

                provider.busy = True
                # Decrement capacity unless we're out of caps and overriding anyway
                if (not override_caps) or (provider.remaining_today > 0):
                    provider.remaining_today -= 1
                served_someone = True

                # Waiting time from queue-enter to pickup
                if patient.last_queue_enter is not None:
                    wait = self.env.now - patient.last_queue_enter
                    patient.waits.append(wait)
                    patient.last_queue_enter = None

                # Mark seen
                if patient.ever_seen == 0:
                    patient.ever_seen = 1
                current_day = int(self.env.now // DAY)
                patient.last_seen_day = current_day

                # Doctor-specific pre-treatment buffer
                if provider.kind == "doctor":
                    if patient.status == CRITICAL:
                        buf = random.uniform(DOC_BUFFER_CRIT_MIN, DOC_BUFFER_CRIT_MAX)
                    else:
                        buf = random.uniform(DOC_BUFFER_NORM_MIN, DOC_BUFFER_NORM_MAX)
                    yield self.env.timeout(buf)

                # Service time
                if provider.kind == "nurse":
                    service = random.uniform(NURSE_SERVICE_MIN, NURSE_SERVICE_MAX)
                else:
                    if patient.status == CRITICAL:
                        service = random.uniform(SERVICE_CRIT_MIN, SERVICE_CRIT_MAX)
                    else:
                        service = random.uniform(SERVICE_NORM_MIN, SERVICE_NORM_MAX)

                # Truncate if they will discharge mid-service
                remaining = max(0, patient.discharge_time - int(self.env.now))
                actual_service = min(service, remaining)
                if actual_service > 0:
                    yield self.env.timeout(actual_service)
                patient.num_visits += 1

                # Release provider
                provider.busy = False

                # Post-service: discharge or cooldown-requeue
                if self.env.now >= patient.discharge_time:
                    self.discharge(patient)
                else:
                    cd = min(COOLDOWN, max(0, patient.discharge_time - int(self.env.now)))
                    if cd > 0:
                        yield self.env.timeout(cd)
                    if patient.in_system and self.env.now < patient.discharge_time:
                        # Re-queue after cooldown and stamp the enqueue time
                        patient.last_queue_enter = int(self.env.now)
                        if patient.status == CRITICAL:
                            yield self.crit_queue.put(patient)
                        else:
                            yield self.norm_queue.put(patient)

            if not served_someone:
                yield self.env.timeout(1)

    # ---------- Midnight resets: provider capacities ----------
    def midnight_resets(self):
        while self.env.now < SIM_TIME:
            mins_today = int(self.env.now) % DAY
            to_midnight = DAY - mins_today if mins_today != 0 else DAY
            yield self.env.timeout(to_midnight)

            for p in self.providers:
                if p.kind == "doctor":
                    p.remaining_today = p.daily_capacity
                else:
                    p.daily_capacity = random.randint(*NURSE_DAILY_CAP_RANGE)
                    p.remaining_today = p.daily_capacity

    # ---------- Daily status flips ----------
    def daily_status_flips(self):
        while self.env.now < SIM_TIME:
            mins_today = int(self.env.now) % DAY
            to_midnight = DAY - mins_today if mins_today != 0 else DAY
            yield self.env.timeout(to_midnight)

            for pt in list(self.active_patients):
                if not pt.in_system:
                    continue
                if pt.status == CRITICAL and random.random() < P_CRIT_TO_NORM:
                    pt.status = NORMAL
                elif pt.status == NORMAL and random.random() < P_NORM_TO_CRIT:
                    pt.status = CRITICAL

    # ---------- Discharge ----------
    def discharge(self, patient: Patient):
        if patient.in_system:
            patient.in_system = False
            if patient in self.active_patients:
                self.active_patients.remove(patient)


# -----------------------
# Running & Output
# -----------------------
def write_csv(sim: HospitalSim, path: str, limit_patients: int = 100):
    pts = sorted(sim.patients, key=lambda p: p.pid)[:limit_patients]
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "patient_id",
            "num_visits",
            "avg_wait_minutes",
            "days_in_hospital",
        ])
        for p in pts:
            avg_wait = (sum(p.waits) / len(p.waits)) if p.waits else 0.0
            days_in_hospital = (p.discharge_time - p.admitted_time) / DAY
            w.writerow([
                p.pid,
                p.num_visits,
                round(avg_wait, 2),
                round(days_in_hospital, 2),
            ])


def main():
    env = simpy.Environment()
    sim = HospitalSim(env)
    env.run(until=SIM_TIME)
    write_csv(sim, CSV_PATH, CSV_LIMIT_PATIENTS)
    print(f"Simulation complete. Wrote CSV: {CSV_PATH}")


if __name__ == "__main__":
    main()

