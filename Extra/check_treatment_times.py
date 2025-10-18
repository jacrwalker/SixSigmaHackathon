import pandas as pd

df = pd.read_csv('scratch_waiting_times_system.csv')

print('='*60)
print('TREATMENT TIME STATISTICS')
print('='*60)
print(f'Average treatment time: {df["treatment_time_days"].mean():.2f} days')
print(f'Min treatment time: {df["treatment_time_days"].min():.2f} days')
print(f'Max treatment time: {df["treatment_time_days"].max():.2f} days')
print(f'Average waiting time: {df["waiting_time_days"].mean():.2f} days')
print('='*60)
print('\nDETAILED VIEW (First 20 patients):')
print(df[['patient_id', 'initial_severity', 'final_severity', 'waiting_time_days', 'treatment_time_days']].head(20).to_string())
print('='*60)
