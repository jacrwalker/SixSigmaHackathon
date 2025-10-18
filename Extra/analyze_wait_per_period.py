"""
Focused Analysis: Why is average waiting time per period uncorrelated with initial severity?

Key metric: average_waiting_period_minutes
Expected: Higher initial severity → less waiting per period (due to priority)
Actual: Correlation r = -0.009 (essentially zero)
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

df = pd.read_csv("scratch_waiting_times_system.csv")

print("="*80)
print("ANALYSIS: Average Waiting Time Per Period vs Initial Severity")
print("="*80)
print()

# Calculate correlation
corr = df['average_waiting_period_minutes'].corr(df['initial_severity'])
print(f"Correlation: r = {corr:.3f} (near-zero!)")
print()

print("THE PROBLEM: Current Severity Drives Priority, Not Initial Severity")
print("-" * 80)
print()
print("Line 124 in simulation.py:")
print("  active_patients.sort(key=lambda p: p.severity, reverse=True)")
print()
print("This sorts by CURRENT severity (p.severity), which changes every minute:")
print("  - While waiting: severity += 0.5 per minute")
print("  - While treated: severity -= 0.5 per minute (if maintain=0)")
print("  - After session: severity += 0.5 (session-end bump)")
print("  - Every 12 hours: severity *= 1.10 for 10% of <50 patients")
print()
print("Result: A patient's priority position FLUCTUATES throughout their stay")
print()

# Show examples of severity changes
print("EXAMPLE TRAJECTORIES:")
print("-" * 80)
print()

# Find patients with different initial severities
low_patient = df[df['initial_severity'] < 30].iloc[0] if len(df[df['initial_severity'] < 30]) > 0 else None
mid_patient = df[(df['initial_severity'] >= 40) & (df['initial_severity'] < 60)].iloc[0] if len(df[(df['initial_severity'] >= 40) & (df['initial_severity'] < 60)]) > 0 else None
high_patient = df[df['initial_severity'] > 70].iloc[0] if len(df[df['initial_severity'] > 70]) > 0 else None

for label, patient in [("LOW", low_patient), ("MID", mid_patient), ("HIGH", high_patient)]:
    if patient is not None:
        print(f"{label} Initial Severity Patient: {patient['patient_id']}")
        print(f"  Initial: {patient['initial_severity']:.0f} → Final: {patient['final_severity']:.1f}")
        print(f"  Change: {patient['final_severity'] - patient['initial_severity']:.1f}")
        print(f"  Avg wait per period: {patient['average_waiting_period_minutes']:.1f} minutes")
        print(f"  Number of sessions: {patient['n_waiting_periods']:.0f}")
        print()

print("WHY CURRENT SEVERITY DOMINATES:")
print("-" * 80)
print()
print("Scenario 1: Low-initial patient (severity 20)")
print("  - Waits 100 minutes → severity climbs to 70")
print("  - Gets HIGH priority (sorted by current=70, not initial=20)")
print("  - Assigned quickly in subsequent periods")
print()
print("Scenario 2: High-initial patient (severity 80)")
print("  - Gets treated, severity drops to 30")
print("  - Gets LOW priority (sorted by current=30, not initial=80)")
print("  - Waits longer in subsequent periods")
print()
print("Scenario 3: Session-end bump disrupts priority")
print("  - Patient at severity 10 finishes treatment")
print("  - Bumped to 10.5, then waits and grows to 60+")
print("  - Now gets medium-high priority despite being 'recovered'")
print()

# Calculate average severity change
avg_severity_change = df['final_severity'].mean() - df['initial_severity'].mean()
pct_increased = (df['final_severity'] > df['initial_severity']).sum() / len(df) * 100
pct_decreased = (df['final_severity'] < df['initial_severity']).sum() / len(df) * 100

print("SEVERITY DYNAMICS OVER FULL STAY:")
print("-" * 80)
print(f"Average initial severity: {df['initial_severity'].mean():.1f}")
print(f"Average final severity: {df['final_severity'].mean():.1f}")
print(f"Average change: {avg_severity_change:.1f}")
print(f"Patients with increased severity: {pct_increased:.1f}%")
print(f"Patients with decreased severity: {pct_decreased:.1f}%")
print()
print("Most patients END with different severity than they STARTED")
print("→ Their priority ranking changes throughout their stay")
print("→ Initial severity ≠ sustained priority position")
print()

# Visualize the disconnect
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Plot 1: Avg wait per period vs initial severity
ax = axes[0]
ax.scatter(df['initial_severity'], df['average_waiting_period_minutes'], 
           alpha=0.7, edgecolor='k', s=60)
# Add trendline
if len(df) >= 2:
    z = np.polyfit(df['initial_severity'], df['average_waiting_period_minutes'], 1)
    p = np.poly1d(z)
    x_line = np.linspace(df['initial_severity'].min(), df['initial_severity'].max(), 100)
    ax.plot(x_line, p(x_line), "r--", alpha=0.8, linewidth=2, 
            label=f'Trendline (r={corr:.3f})')
ax.set_xlabel('Initial Severity', fontsize=12)
ax.set_ylabel('Avg Waiting Time Per Period (min)', fontsize=12)
ax.set_title(f'Avg Wait Per Period vs Initial Severity\n(r={corr:.3f} - No Correlation!)', fontsize=13)
ax.legend()
ax.grid(True, alpha=0.3)

# Plot 2: Initial vs final severity to show dynamics
ax = axes[1]
ax.scatter(df['initial_severity'], df['final_severity'], alpha=0.7, edgecolor='k', s=60)
ax.plot([0, 100], [0, 100], 'k--', alpha=0.5, linewidth=1, label='No change line')
ax.set_xlabel('Initial Severity', fontsize=12)
ax.set_ylabel('Final Severity', fontsize=12)
ax.set_title('Initial vs Final Severity\n(Shows Severity Changes During Stay)', fontsize=13)
ax.legend()
ax.grid(True, alpha=0.3)
ax.set_xlim(0, 105)
ax.set_ylim(0, 105)

plt.tight_layout()
plt.savefig('wait_per_period_analysis.png', dpi=150)
print("✓ Visualization saved to: wait_per_period_analysis.png")
print()

print("="*80)
print("CONCLUSION")
print("="*80)
print()
print("Initial severity does NOT predict average waiting time per period because:")
print()
print("1. Priority is determined by CURRENT severity (line 124)")
print("   → Current severity changes constantly (+0.5/min waiting, -0.5/min treated)")
print()
print("2. Session-end bump (+0.5) and 12-hour upgrades (×1.10) disrupt rankings")
print("   → Patients who were low-priority become high-priority and vice versa")
print()
print("3. Most patients end with different severity than they started")
print(f"   → {pct_increased:.0f}% increased, {pct_decreased:.0f}% decreased")
print("   → Initial severity ≠ sustained priority throughout stay")
print()
print("="*80)
print()
print("TO FIX: Sort by initial_severity instead of current severity")
print("  Line 124: active_patients.sort(key=lambda p: p.initial_severity, reverse=True)")
print()
print("This would create sustained priority based on admission severity.")
print("="*80)
