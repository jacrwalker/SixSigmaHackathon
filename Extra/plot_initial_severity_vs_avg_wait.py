import os
import sys
import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def main(csv_path: str = "scratch_waiting_times_system.csv") -> int:
    if not os.path.exists(csv_path):
        print(f"CSV not found: {csv_path}")
        return 1

    df = pd.read_csv(csv_path)

    # Fallback if the column isn't present: compute from totals
    if "average_waiting_period_minutes" not in df.columns:
        if {"waiting_time_minutes", "n_waiting_periods"}.issubset(df.columns):
            df["average_waiting_period_minutes"] = df.apply(
                lambda r: r["waiting_time_minutes"] / r["n_waiting_periods"] if r["n_waiting_periods"] else np.nan,
                axis=1,
            )
        else:
            print("Required columns not found in CSV.")
            return 2

    # Filter to valid rows
    plot_df = df[["initial_severity", "average_waiting_period_minutes"]].dropna()
    plot_df = plot_df[(plot_df["initial_severity"].between(1, 100)) & (plot_df["average_waiting_period_minutes"] >= 0)]

    if plot_df.empty:
        print("No valid data to plot.")
        return 3

    x = plot_df["initial_severity"].values
    y = plot_df["average_waiting_period_minutes"].values

    # Basic stats
    corr = np.corrcoef(x, y)[0, 1] if len(plot_df) > 1 else np.nan
    x_mean = float(np.mean(x)) if len(x) else float("nan")
    y_mean = float(np.mean(y)) if len(y) else float("nan")

    plt.figure(figsize=(9, 6))
    plt.scatter(x, y, alpha=0.7, edgecolor="k", linewidth=0.5)

    # Add simple linear trendline if we have enough points
    if len(plot_df) >= 2 and not math.isnan(corr):
        m, b = np.polyfit(x, y, 1)
        x_line = np.linspace(min(x), max(x), 100)
        y_line = m * x_line + b
        plt.plot(x_line, y_line, color="tab:orange", label=f"Trendline (r={corr:.2f})")
        plt.legend()

    plt.title("Avg Waiting Time per Period vs Initial Severity")
    plt.xlabel("Initial Severity (1–100)")
    plt.ylabel("Average Waiting Time per Waiting Period (minutes)")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    out_path = "initial_severity_vs_avg_wait.png"
    plt.savefig(out_path, dpi=150)
    print(f"Saved plot to {out_path}")
    print(f"Points: {len(plot_df)} | Mean X (init sev): {x_mean:.2f} | Mean Y (avg wait/min): {y_mean:.2f} | r={corr:.3f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
