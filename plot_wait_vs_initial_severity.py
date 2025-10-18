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

    required = {"initial_severity", "waiting_time_minutes", "final_severity"}
    if not required.issubset(df.columns):
        print(f"CSV missing required columns: {required - set(df.columns)}")
        return 2

    # Compute severity change to color points (negative = improved)
    df["severity_change"] = df["final_severity"] - df["initial_severity"]

    plot_df = df[["initial_severity", "waiting_time_minutes", "severity_change"]].dropna()
    plot_df = plot_df[(plot_df["initial_severity"].between(1, 100)) & (plot_df["waiting_time_minutes"] >= 0)]
    if plot_df.empty:
        print("No valid data to plot.")
        return 3

    x = plot_df["initial_severity"].values
    y = plot_df["waiting_time_minutes"].values
    delta = plot_df["severity_change"].values

    corr = np.corrcoef(x, y)[0, 1] if len(plot_df) > 1 else np.nan

    # Color by improvement vs worsening
    colors = np.where(delta <= 0, "tab:green", "tab:red")

    plt.figure(figsize=(9, 6))
    plt.scatter(x, y, c=colors, alpha=0.8, edgecolor="k", linewidth=0.5)

    # Add simple linear trendline
    if len(plot_df) >= 2 and not math.isnan(corr):
        m, b = np.polyfit(x, y, 1)
        x_line = np.linspace(min(x), max(x), 100)
        y_line = m * x_line + b
        plt.plot(x_line, y_line, color="tab:orange", label=f"Trendline (r={corr:.2f})")

    # Build legend for colors
    from matplotlib.lines import Line2D
    legend_elems = [
        Line2D([0], [0], marker='o', color='w', label='Severity decreased', markerfacecolor='tab:green', markeredgecolor='k', markersize=8),
        Line2D([0], [0], marker='o', color='w', label='Severity increased', markerfacecolor='tab:red', markeredgecolor='k', markersize=8),
    ]
    if len(plot_df) >= 2 and not math.isnan(corr):
        legend_elems.append(Line2D([0], [0], color='tab:orange', lw=2, label=f'Trendline (r={corr:.2f})'))
    plt.legend(handles=legend_elems, loc='best')

    plt.title("Total Waiting Time vs Initial Severity")
    plt.xlabel("Initial Severity (1–100)")
    plt.ylabel("Total Waiting Time (minutes)")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    out_path = "wait_vs_initial_severity.png"
    plt.savefig(out_path, dpi=150)
    print(f"Saved plot to {out_path}")
    print(f"Points: {len(plot_df)} | Corr(initial severity, waiting minutes) r={corr:.3f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
