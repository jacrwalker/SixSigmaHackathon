"""
Main entry point for the hospital simulation per config rules.
"""

import pandas as pd
from simulation import Simulation
from config import OUTPUT_CSV


def main():
    print("\n" + "=" * 60)
    print("STARTING HOSPITAL SIMULATION (FROM-SCRATCH BRANCH)")
    print("=" * 60)
    sim = Simulation()
    print("Running simulation...")
    sim.run()
    print("\u2713 Simulation complete!\n")
    report = sim.get_waiting_time_report()
    df = pd.DataFrame(report)
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"\u2713 Waiting times exported to: {OUTPUT_CSV}\n")
    # Display key columns
    display_cols = [
        'patient_id', 'initial_severity', 'final_severity',
        'waiting_time_minutes', 'average_waiting_period_minutes', 'n_waiting_periods'
    ]
    if not df.empty:
        print(df[display_cols].head(20).to_string(index=False))
    print("=" * 60)
    print("SIMULATION FINISHED")
    print("=" * 60)


if __name__ == "__main__":
    main()
"""
Main entry point for the rewritten hospital simulation (fresh branch)
"""

import pandas as pd
from simulation import Simulation
from config import OUTPUT_CSV

def main():
    print("\n" + "="*60)
    print("STARTING HOSPITAL SIMULATION (FRESH BRANCH)")
    print("="*60)
    sim = Simulation()
    print("Running simulation...")
    sim.run()
    print("✓ Simulation complete!\n")
    report = sim.get_waiting_time_report()
    df = pd.DataFrame(report)
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"✓ Waiting times exported to: {OUTPUT_CSV}\n")
    # Show new columns in printout
    display_cols = [
        'patient_id', 'initial_severity', 'waiting_time_minutes', 'waiting_time_days',
        'average_waiting_period_minutes', 'average_waiting_period_days', 'waiting_periods'
    ]
    print(df[display_cols].head(20).to_string(index=False))
    print("="*60)
    print("SIMULATION FINISHED")
    print("="*60)

if __name__ == "__main__":
    main()
