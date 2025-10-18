"""
Diagnostic analysis: Why isn't there a negative correlation between initial severity and waiting time?

This script analyzes the simulation data to understand the competing effects.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Read the CSV
df = pd.read_csv("scratch_waiting_times_system.csv")

# Calculate key metrics
df['severity_change'] = df['final_severity'] - df['initial_severity']
df['total_time_days'] = df['waiting_time_days'] + df['treatment_time_days']
df['wait_to_treatment_ratio'] = df['waiting_time_days'] / (df['treatment_time_days'] + 0.001)
df['avg_session_duration'] = df['treatment_time_minutes'] / df['n_waiting_periods']

# Separate by initial severity ranges
low_sev = df[df['initial_severity'] < 50]
high_sev = df[df['initial_severity'] >= 50]

print("="*80)
print("SIMULATION LOGIC ANALYSIS")
print("="*80)
print()

print("KEY INSIGHT: Initial Severity Sets Discharge Window")
print("-" * 80)
print(f"Low initial severity (<50):")
print(f"  - Discharge window: 3-7 days")
print(f"  - Actual avg total time: {low_sev['total_time_days'].mean():.2f} days")
print(f"  - Actual avg waiting: {low_sev['waiting_time_days'].mean():.2f} days")
print(f"  - N patients: {len(low_sev)}")
print()
print(f"High initial severity (≥50):")
print(f"  - Discharge window: 3-28 days")
print(f"  - Actual avg total time: {high_sev['total_time_days'].mean():.2f} days")
print(f"  - Actual avg waiting: {high_sev['waiting_time_days'].mean():.2f} days")
print(f"  - N patients: {len(high_sev)}")
print()

print("COMPETING EFFECT #1: Longer Stays → More Total Waiting")
print("-" * 80)
print("Even with priority treatment, high-severity patients stay longer overall,")
print("accumulating more total waiting minutes across multiple sessions.")
print()

# Correlation analysis
corr_wait_init = df['waiting_time_minutes'].corr(df['initial_severity'])
corr_avgwait_init = df['average_waiting_period_minutes'].corr(df['initial_severity'])
corr_sessions_init = df['n_waiting_periods'].corr(df['initial_severity'])

print("COMPETING EFFECT #2: Current Severity Drives Priority (Not Initial)")
print("-" * 80)
print(f"Correlation: initial_severity vs total_waiting_minutes = {corr_wait_init:.3f}")
print(f"Correlation: initial_severity vs avg_wait_per_period = {corr_avgwait_init:.3f}")
print(f"Correlation: initial_severity vs number_of_sessions = {corr_sessions_init:.3f}")
print()
print("Why avg_wait_per_period is near-zero correlation:")
print("  - Current severity (not initial) determines queue position each minute")
print("  - Patients' severity changes constantly due to waiting (+0.5/min) and treatment (-0.5/min)")
print("  - A low-initial patient can climb high in queue after waiting")
print("  - A high-initial patient can drop low in queue after treatment")
print()

print("COMPETING EFFECT #3: Session-End Bump (+0.5)")
print("-" * 80)
print("After each treatment session ends:")
print("  - Severity increases by +0.5")
print("  - This partially offsets decay during treatment")
print("  - Creates cycle: treat → bump → wait → grow → treat → bump...")
print()

print("COMPETING EFFECT #4: 12-Hour Severity Upgrades")
print("-" * 80)
print("Every 12 hours, 10% of patients with severity < 50 get 10% bump")
print("  - Pushes low-severity patients higher in queue unexpectedly")
print("  - Disrupts sustained priority based on initial severity")
print()

# Show example trajectories
print("EXAMPLE: Comparing Two Patients")
print("-" * 80)
if len(df) >= 2:
    # Find one low-sev and one high-sev patient
    low_example = low_sev.iloc[0] if len(low_sev) > 0 else None
    high_example = high_sev.iloc[0] if len(high_sev) > 0 else None
    
    if low_example is not None:
        print(f"LOW initial severity patient: {low_example['patient_id']}")
        print(f"  Initial severity: {low_example['initial_severity']:.1f}")
        print(f"  Final severity: {low_example['final_severity']:.1f}")
        print(f"  Total days in hospital: {low_example['total_time_days']:.2f}")
        print(f"  Days waiting: {low_example['waiting_time_days']:.2f}")
        print(f"  Days treated: {low_example['treatment_time_days']:.2f}")
        print(f"  Number of sessions: {low_example['n_waiting_periods']:.0f}")
        print(f"  Avg wait per session: {low_example['average_waiting_period_minutes']:.1f} min")
        print()
    
    if high_example is not None:
        print(f"HIGH initial severity patient: {high_example['patient_id']}")
        print(f"  Initial severity: {high_example['initial_severity']:.1f}")
        print(f"  Final severity: {high_example['final_severity']:.1f}")
        print(f"  Total days in hospital: {high_example['total_time_days']:.2f}")
        print(f"  Days waiting: {high_example['waiting_time_days']:.2f}")
        print(f"  Days treated: {high_example['treatment_time_days']:.2f}")
        print(f"  Number of sessions: {high_example['n_waiting_periods']:.0f}")
        print(f"  Avg wait per session: {high_example['average_waiting_period_minutes']:.1f} min")
        print()
        
        if low_example is not None:
            print("COMPARISON:")
            print(f"  High-sev patient waited {high_example['waiting_time_days'] - low_example['waiting_time_days']:.2f} MORE days")
            print(f"  ...but stayed {high_example['total_time_days'] - low_example['total_time_days']:.2f} MORE days total")
            print(f"  So more waiting is due to LONGER STAY, not lower priority")
            print()

print("="*80)
print("CONCLUSION: Why No Negative Correlation")
print("="*80)
print("Initial severity affects discharge window (3-28 days for high, 3-7 for low),")
print("but CURRENT severity (which changes minute-by-minute) drives priority.")
print()
print("High initial severity → longer stay → more sessions → more total waiting")
print("  ...even if they get treated faster when severity is high.")
print()
print("To see 'higher initial severity → less waiting', you would need:")
print("  1. Discharge based on severity reaching a threshold (not time windows)")
print("  2. OR remove session-end bump and upgrades to preserve initial severity ranking")
print("  3. OR dramatically increase staff so high-sev patients rarely wait")
print("="*80)

# Create visualization
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Plot 1: Total waiting vs initial severity (with discharge window annotation)
ax = axes[0, 0]
ax.scatter(low_sev['initial_severity'], low_sev['waiting_time_days'], 
           alpha=0.6, label='Initial <50 (3-7 day window)', color='tab:blue')
ax.scatter(high_sev['initial_severity'], high_sev['waiting_time_days'], 
           alpha=0.6, label='Initial ≥50 (3-28 day window)', color='tab:red')
ax.set_xlabel('Initial Severity')
ax.set_ylabel('Total Waiting Time (days)')
ax.set_title(f'Total Waiting vs Initial Severity\n(r={corr_wait_init:.3f})')
ax.legend()
ax.grid(True, alpha=0.3)

# Plot 2: Avg wait per period vs initial severity
ax = axes[0, 1]
ax.scatter(df['initial_severity'], df['average_waiting_period_minutes'], alpha=0.6, edgecolor='k')
ax.set_xlabel('Initial Severity')
ax.set_ylabel('Avg Wait Per Period (min)')
ax.set_title(f'Avg Wait Per Period vs Initial Severity\n(r={corr_avgwait_init:.3f} - near zero!)')
ax.grid(True, alpha=0.3)

# Plot 3: Number of sessions vs initial severity
ax = axes[1, 0]
ax.scatter(low_sev['initial_severity'], low_sev['n_waiting_periods'], 
           alpha=0.6, label='Initial <50', color='tab:blue')
ax.scatter(high_sev['initial_severity'], high_sev['n_waiting_periods'], 
           alpha=0.6, label='Initial ≥50', color='tab:red')
ax.set_xlabel('Initial Severity')
ax.set_ylabel('Number of Sessions')
ax.set_title(f'Number of Sessions vs Initial Severity\n(r={corr_sessions_init:.3f})')
ax.legend()
ax.grid(True, alpha=0.3)

# Plot 4: Total time vs initial severity
ax = axes[1, 1]
ax.scatter(low_sev['initial_severity'], low_sev['total_time_days'], 
           alpha=0.6, label='Initial <50 (3-7 day window)', color='tab:blue')
ax.scatter(high_sev['initial_severity'], high_sev['total_time_days'], 
           alpha=0.6, label='Initial ≥50 (3-28 day window)', color='tab:red')
ax.set_xlabel('Initial Severity')
ax.set_ylabel('Total Time in Hospital (days)')
ax.set_title('Total Time vs Initial Severity\n(Longer windows = more total time)')
ax.legend()
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('simulation_logic_analysis.png', dpi=150)
print("\n✓ Visualization saved to: simulation_logic_analysis.png")
