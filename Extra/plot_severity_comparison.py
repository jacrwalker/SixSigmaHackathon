"""
Plot comparison of initial vs final severity with squared decay function
"""
import pandas as pd
import matplotlib.pyplot as plt

# Read the CSV
df = pd.read_csv('scratch_waiting_times_system.csv')

# Create scatter plot
plt.figure(figsize=(10, 6))
plt.scatter(df['initial_severity'], df['final_severity'], alpha=0.6, s=100, c='blue', edgecolors='black')
plt.plot([0, 100], [0, 100], 'r--', linewidth=2, label='No change line')
plt.xlabel('Initial Severity', fontsize=12)
plt.ylabel('Final Severity', fontsize=12)
plt.title('Initial vs Final Severity (Squared Decay Function)', fontsize=14, fontweight='bold')
plt.grid(True, alpha=0.3)
plt.legend(fontsize=10)
plt.xlim(0, 105)
plt.ylim(0, 105)
plt.tight_layout()
plt.savefig('initial_vs_final_severity.png', dpi=150)
print('✓ Plot saved as initial_vs_final_severity.png')

# Print summary statistics
print('\n' + '='*60)
print('SUMMARY STATISTICS')
print('='*60)
print(f'Total patients discharged: {len(df)}')
print(f'Average Initial Severity: {df["initial_severity"].mean():.2f}')
print(f'Average Final Severity: {df["final_severity"].mean():.2f}')
print(f'Average Severity Reduction: {(df["initial_severity"] - df["final_severity"]).mean():.2f}')
print(f'Patients discharged at severity 1.0: {(df["final_severity"] == 1.0).sum()} / {len(df)} ({(df["final_severity"] == 1.0).sum()/len(df)*100:.1f}%)')
print(f'Patients with reduced severity: {(df["final_severity"] < df["initial_severity"]).sum()} / {len(df)} ({(df["final_severity"] < df["initial_severity"]).sum()/len(df)*100:.1f}%)')
print(f'Patients with increased severity: {(df["final_severity"] > df["initial_severity"]).sum()} / {len(df)} ({(df["final_severity"] > df["initial_severity"]).sum()/len(df)*100:.1f}%)')
print('='*60)
