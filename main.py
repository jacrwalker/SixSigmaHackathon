"""
Main entry point for the hospital simulation (NEW SYSTEM)

This script runs the new hospital system simulation and outputs
patient waiting times in a clean format.
"""

import pandas as pd
import numpy as np
from simulation import HospitalSimulation
from config import MINUTES_PER_DAY, SIM_DAYS


def print_summary_statistics(results):
    """Print summary statistics from the simulation"""
    discharged = results['discharged_patients']
    
    if not discharged:
        print("No patients discharged during simulation period.")
        return
    
    # Calculate statistics
    avg_stay = np.mean([p['total_time_in_hospital'] for p in discharged]) / MINUTES_PER_DAY
    avg_wait = np.mean([p['total_wait_time'] for p in discharged]) / MINUTES_PER_DAY
    mean_severity = np.mean([p['severity'] for p in discharged])
    
    print("\n" + "="*60)
    print("SIMULATION SUMMARY STATISTICS (NEW SYSTEM)")
    print("="*60)
    print(f"Simulation duration: {SIM_DAYS} days")
    print(f"Maximum bed capacity: {results['max_capacity']}")
    print(f"Total discharged patients: {results['total_discharged']}")
    print(f"Remaining active patients: {results['total_active']}")
    print(f"Rejected admissions (no beds): {results['rejected_admissions']}")
    print(f"Average hospital stay: {avg_stay:.2f} days")
    print(f"Average waiting time: {avg_wait:.2f} days")
    print(f"Mean final severity: {mean_severity:.2f}")
    print("="*60 + "\n")


def export_waiting_times(report, filename='waiting_times_new_system.csv'):
    """Export patient waiting times to CSV"""
    df = pd.DataFrame(report)
    df.to_csv(filename, index=False)
    print(f"✓ Waiting times exported to: {filename}\n")


def display_waiting_times(report, n_rows=20):
    """Display waiting times in a formatted table"""
    df = pd.DataFrame(report)
    
    print("\n" + "="*60)
    print("PATIENT WAITING TIMES (NEW SYSTEM)")
    print("="*60)
    print(f"Showing first {min(n_rows, len(df))} of {len(df)} patients:\n")
    
    # Format for display
    display_df = df[['patient_id', 'waiting_time_days']].copy()
    display_df['waiting_time_days'] = display_df['waiting_time_days'].round(2)
    
    print(display_df.head(n_rows).to_string(index=False))
    print("\n" + "="*60 + "\n")


def main():
    """Main execution function"""
    print("\n" + "="*60)
    print("STARTING HOSPITAL SIMULATION (NEW SYSTEM)")
    print("="*60)
    print("Configuration:")
    print(f"  - Simulation period: {SIM_DAYS} days")
    print(f"  - Maximum bed capacity: 25 patients (one hospital section)")
    print(f"  - Initial patients: 20")
    print(f"  - Staff ratios:")
    print(f"    • Doctors: 1:20-25 (1 doctor)")
    print(f"    • Nurses: 1:3-4 (7 nurses)")
    print(f"  - Daily admissions: Poisson(mean=2)")
    print(f"  - Discharge thresholds:")
    print(f"    • Severity < 50: 4 days")
    print(f"    • Severity >= 50: 8 days")
    print(f"\n  - Severity Dynamics (Gas Pedal System):")
    print(f"    • When WAITING: +0.1 per minute")
    print(f"    • When SEEN (maintain=False): -0.5 x admission_severity per minute")
    print(f"    • When SEEN (maintain=True): no change")
    print("="*60 + "\n")
    
    # Run simulation
    print("Running simulation...")
    sim = HospitalSimulation()
    sim.run()
    print("✓ Simulation complete!\n")
    
    # Get results
    results = sim.get_results()
    waiting_time_report = sim.get_waiting_time_report()
    
    # Print summary statistics
    print_summary_statistics(results)
    
    # Display waiting times
    display_waiting_times(waiting_time_report)
    
    # Export to CSV
    export_waiting_times(waiting_time_report)
    
    print("="*60)
    print("SIMULATION FINISHED")
    print("="*60)


if __name__ == "__main__":
    main()
