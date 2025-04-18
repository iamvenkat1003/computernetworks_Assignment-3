import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# Step 1: Read RTT data from CSV
data = pd.read_csv("graphs-1/rtt_summary.csv")

# Step 2: Calculate average RTT values for each scheme
averages = data.groupby("Scheme")[["Avg RTT", "95th RTT"]].mean().reset_index()

# Step 3: Make sure the folder to save plots exists
os.makedirs("graphs-1", exist_ok=True)

# Step 4: Set up positions and bar width for grouped bars
bar_width = 0.4
x_pos = np.arange(len(averages))  # One position per scheme

# Step 5: Choose two clear colors
color_avg = "steelblue"       # for average RTT
color_95th = "darkorange"     # for 95th percentile RTT

# Step 6: Create the bar chart
plt.figure(figsize=(8, 6))
plt.bar(x_pos, averages["Avg RTT"], width=bar_width, color=color_avg, label="Average RTT (ms)")
plt.bar(x_pos + bar_width, averages["95th RTT"], width=bar_width, color=color_95th, label="95th Percentile RTT (ms)")

plt.xticks(x_pos + bar_width / 2, averages["Scheme"].str.upper())
plt.ylabel("RTT (ms)")
plt.title("RTT Comparison by Congestion Control Scheme")
plt.legend()
plt.grid(axis='y', linestyle='--', alpha=0.4)
plt.tight_layout()

plt.savefig("graphs-1/rtt_bar_chart.png")

