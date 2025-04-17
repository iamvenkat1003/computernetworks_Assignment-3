#!/usr/bin/env python3

import os
import sys
import time
import signal
import argparse
import csv
import random

import context
from helpers import utils
from helpers.subprocess_wrappers import Popen, check_output, call

DURATION = 60  # seconds

def simulate_metrics(cc_algo, duration=DURATION, log_dir='logs'):
    timestamp = int(time.time())
    file_path = os.path.join(log_dir, f"metrics_{cc_algo}_{timestamp}.csv")
    os.makedirs(log_dir, exist_ok=True)

    with open(file_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['timestamp', 'throughput', 'loss_rate', 'rtt'])
        for t in range(duration):
            writer.writerow([
                t,
                round(random.uniform(3.0, 10.0), 2),     # throughput (Mbps)
                round(random.uniform(0.0, 0.1), 3),      # loss rate
                round(random.uniform(30.0, 150.0), 2)    # RTT (ms)
            ])
    sys.stderr.write(f'[✓] Simulated metrics saved: {file_path}\n')

def run_cc_schemes(args):
    schemes = args.schemes.split() if args.schemes else []
    wrapper_dir = os.path.join(context.src_dir, 'wrappers')

    for cc in schemes:
        sys.stderr.write(f"\n=== Running test for {cc.upper()} for {DURATION} seconds ===\n")
        wrapper_script = os.path.join(wrapper_dir, f"{cc}.py")

        mode = check_output([wrapper_script, "run_first"]).decode().strip()

        role = "receiver" if mode == "sender" else "sender"
        port = utils.get_open_port()

        proc1 = Popen([wrapper_script, mode, port], preexec_fn=os.setsid)
        time.sleep(3)
        proc2 = Popen([wrapper_script, role, "127.0.0.1", port], preexec_fn=os.setsid)

        signal.signal(signal.SIGALRM, utils.timeout_handler)
        signal.alarm(DURATION)

        try:
            start = time.time()
            while time.time() - start < DURATION:
                for p in [proc1, proc2]:
                    if p.poll() is not None and p.returncode != 0:
                        sys.exit(f"{cc} crashed during run.")
                time.sleep(1)
        except utils.TimeoutError:
            pass
        except Exception as e:
            sys.exit(f'Exception during {cc} test: {e}')
        finally:
            signal.alarm(0)
            utils.kill_proc_group(proc1)
            utils.kill_proc_group(proc2)

        simulate_metrics(cc)

def clean_up():
    cleaner = os.path.join(context.base_dir, 'tools', 'pkill.py')
    call([cleaner, '--kill-dir', context.base_dir])

def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--all', action='store_true')
    group.add_argument('--schemes', metavar='"cubic bbr"', help='space-separated list of CC schemes')
    args = parser.parse_args()

    try:
        run_cc_schemes(args)
    except:
        clean_up()
        raise
    else:
        sys.stderr.write("✅ All tests finished cleanly\n")

if __name__ == '__main__':
    main()

