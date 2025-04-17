import os
import pandas as pd
import matplotlib.pyplot as plt
import glob
import subprocess
import shutil

CC_SCHEMES = ["cubic", "bbr", "vegas"]
NETWORK_PROFILES = {
    "1": {
        "delay_ms": 5,
        "downlink": "mahimahi/traces/TMobile-LTE-driving.down",
        "uplink": "mahimahi/traces/TMobile-LTE-driving.up"
    },
    "2": {
        "delay_ms": 200,
        "downlink": "mahimahi/traces/TMobile-LTE-short.down",
        "uplink": "mahimahi/traces/TMobile-LTE-short.up"
    }
}

def get_latest_log_dir():
    logs_dirs = sorted([d for d in os.listdir(".") if d.startswith("logs-") and os.path.isdir(d)])
    return logs_dirs[-1] if logs_dirs else None

def get_new_graphs_dir():
    i = 1
    while os.path.exists(f"graphs-{i}"):
        i += 1
    os.makedirs(f"graphs-{i}", exist_ok=True)
    return f"graphs-{i}"

def run_tests():
    for profile_id, config in NETWORK_PROFILES.items():
        print(f"\n--- Running Profile {profile_id} (RTT ~ {2 * config['delay_ms']}ms) ---")
        for scheme in CC_SCHEMES:
            print(f"[INFO] Running {scheme.upper()}")
            result_path = f"results/profile_{profile_id}/{scheme}"
            os.makedirs(result_path, exist_ok=True)

            cmd = (
                f"mm-delay {config['delay_ms']} "
                f"mm-link {config['downlink']} {config['uplink']} -- "
                f"bash -c 'python3 tests/test_schemes_1.py --schemes \"{scheme}\" > {result_path}/log.txt 2>&1'"
            )

            try:
                subprocess.run(cmd, shell=True, check=True)
                print(f"[SUCCESS] {scheme.upper()} completed.")
            except subprocess.CalledProcessError:
                print(f"[ERROR] {scheme.upper()} failed.")

            log_dir = get_latest_log_dir()
            if log_dir:
                files = sorted(glob.glob(f"{log_dir}/metrics_{scheme}_*.csv"), key=os.path.getmtime, reverse=True)
                if files:
                    shutil.copy(files[0], os.path.join(result_path, f"{scheme}_log.csv"))
                else:
                    print(f"[WARNING] No metrics found for {scheme.upper()} in {log_dir}")
            else:
                print(f"[WARNING] No logs directory found.")

def load_results():
    frames = []
    for profile_id in NETWORK_PROFILES:
        for scheme in CC_SCHEMES:
            csv_path = f'results/profile_{profile_id}/{scheme}/{scheme}_log.csv'
            if os.path.exists(csv_path):
                df = pd.read_csv(csv_path)
                df["scheme"] = scheme
                df["profile"] = profile_id
                df["timestamp"] = list(range(len(df)))
                frames.append(df)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

def plot_all(data, graph_dir):
    for profile in data["profile"].unique():
        plt.figure()
        for scheme in data["scheme"].unique():
            sub = data[(data["profile"] == profile) & (data["scheme"] == scheme)]
            plt.plot(sub["timestamp"], sub["throughput"], label=scheme)
        plt.title(f"Throughput - Profile {profile}")
        plt.xlabel("Time (s)")
        plt.ylabel("Mbps")
        plt.legend()
        plt.grid(True)
        plt.savefig(f"{graph_dir}/throughput_profile_{profile}.png")
        plt.close()

        plt.figure()
        for scheme in data["scheme"].unique():
            sub = data[(data["profile"] == profile) & (data["scheme"] == scheme)]
            if "loss_rate" in sub:
                plt.plot(sub["timestamp"], sub["loss_rate"], label=scheme)
        plt.title(f"Loss Rate - Profile {profile}")
        plt.xlabel("Time (s)")
        plt.ylabel("Loss Rate")
        plt.legend()
        plt.grid(True)
        plt.savefig(f"{graph_dir}/loss_profile_{profile}.png")
        plt.close()

    for scheme in data["scheme"].unique():
        df = data[data["scheme"] == scheme]
        plt.figure()
        for profile in df["profile"].unique():
            sub = df[df["profile"] == profile]
            plt.plot(sub["timestamp"], sub["throughput"], label=f"Profile {profile}")
        plt.title(f"Throughput - {scheme}")
        plt.xlabel("Time (s)")
        plt.ylabel("Mbps")
        plt.legend()
        plt.grid(True)
        plt.savefig(f"{graph_dir}/throughput_{scheme}.png")
        plt.close()

        if "loss_rate" in df.columns:
            plt.figure()
            for profile in df["profile"].unique():
                sub = df[df["profile"] == profile]
                plt.plot(sub["timestamp"], sub["loss_rate"], label=f"Profile {profile}")
            plt.title(f"Loss Rate - {scheme}")
            plt.xlabel("Time (s)")
            plt.ylabel("Loss Rate")
            plt.legend()
            plt.grid(True)
            plt.savefig(f"{graph_dir}/loss_{scheme}.png")
            plt.close()

def scatter_rtt_vs_tp(data, graph_dir):
    plt.figure()
    for scheme in data["scheme"].unique():
        for profile in data["profile"].unique():
            sub = data[(data["scheme"] == scheme) & (data["profile"] == profile)]
            if not sub.empty:
                avg_rtt = sub["rtt"].mean()
                avg_tp = sub["throughput"].mean()
                plt.scatter(avg_rtt, avg_tp, label=f"{scheme}-{profile}")
                plt.annotate(f"{scheme}-{profile}", (avg_rtt, avg_tp))
    plt.title("RTT vs Throughput")
    plt.xlabel("Avg RTT (ms)")
    plt.ylabel("Avg Throughput (Mbps)")
    plt.grid(True)
    plt.legend()
    plt.savefig(f"{graph_dir}/rtt_vs_throughput.png")
    plt.close()

def summarize_rtt(data, graph_dir):
    records = []
    for scheme in data["scheme"].unique():
        for profile in data["profile"].unique():
            sub = data[(data["scheme"] == scheme) & (data["profile"] == profile)]
            if not sub.empty:
                mean = sub["rtt"].mean()
                p95 = sub["rtt"].quantile(0.95)
                records.append((scheme, profile, mean, p95))
    df = pd.DataFrame(records, columns=["Scheme", "Profile", "Avg RTT", "95th RTT"])
    df.to_csv(f"{graph_dir}/rtt_summary.csv", index=False)
    print(df.to_string(index=False))

def main():
    graph_dir = get_new_graphs_dir()
    os.makedirs("results", exist_ok=True)

    run_tests()

    df = load_results()
    if df.empty:
        print("[ERROR] No data collected.")
        return

    plot_all(df, graph_dir)
    summarize_rtt(df, graph_dir)
    scatter_rtt_vs_tp(df, graph_dir)

    print(f"[✅ DONE] Results saved in {graph_dir}")

if __name__ == "__main__":
    main()
