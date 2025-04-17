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

TEST_DURATION = 60  # Duration in seconds


def get_new_log_dir(base="logs"):
    """Finds a new logs-N folder to avoid overwriting previous logs."""
    count = 1
    while os.path.exists(f"{base}-{count}"):
        count += 1
    new_dir = f"{base}-{count}"
    os.makedirs(new_dir, exist_ok=True)
    return new_dir


def simulate_metrics(scheme, duration=TEST_DURATION):
    """Simulate metric logs for a CC scheme and save in a logs-N folder."""
    log_dir = get_new_log_dir("logs")
    timestamp = int(time.time())
    filename = os.path.join(log_dir, f"metrics_{scheme}_{timestamp}.csv")

    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['timestamp', 'throughput', 'loss_rate', 'rtt'])
        for t in range(duration):
            throughput = round(random.uniform(3.0, 10.0), 2)
            loss_rate = round(random.uniform(0.0, 0.1), 3)
            rtt = round(random.uniform(30.0, 150.0), 2)
            writer.writerow([t, throughput, loss_rate, rtt])

    sys.stderr.write(f"[✓] Simulated metrics saved: {filename}\n")


def run_cc_schemes(args):
    schemes = args.schemes.split() if args.schemes else []
    wrappers_dir = os.path.join(context.src_dir, 'wrappers')

    for scheme in schemes:
        sys.stderr.write(f"\n=== Running test for {scheme.upper()} for {TEST_DURATION} seconds ===\n")
        wrapper_script = os.path.join(wrappers_dir, f"{scheme}.py")

        try:
            run_first = check_output([wrapper_script, 'run_first']).decode().strip()
        except Exception as e:
            sys.exit(f"[ERROR] Failed to determine run_first for {scheme}: {e}")

        run_second = 'receiver' if run_first == 'sender' else 'sender'
        port = utils.get_open_port()

        # Start the first process
        proc1 = Popen([wrapper_script, run_first, port], preexec_fn=os.setsid)
        time.sleep(3)  # Give the server time to start

        # Start the second process
        proc2 = Popen([wrapper_script, run_second, '127.0.0.1', port], preexec_fn=os.setsid)

        signal.signal(signal.SIGALRM, utils.timeout_handler)
        signal.alarm(TEST_DURATION)

        try:
            start_time = time.time()
            while time.time() - start_time < TEST_DURATION:
                for proc in [proc1, proc2]:
                    if proc.poll() is not None and proc.returncode != 0:
                        raise RuntimeError(f"[ERROR] {scheme} process exited with non-zero code.")
                time.sleep(1)
        except utils.TimeoutError:
            pass
        except Exception as e:
            sys.exit(f"[ERROR] test_schemes.py: {e}")
        finally:
            signal.alarm(0)
            utils.kill_proc_group(proc1)
            utils.kill_proc_group(proc2)

        simulate_metrics(scheme)


def cleanup():
    cleanup_script = os.path.join(context.base_dir, 'tools', 'pkill.py')
    call([cleanup_script, '--kill-dir', context.base_dir])


def main():
    parser = argparse.ArgumentParser()

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--all', action='store_true',
                       help='Test all CC schemes from config')
    group.add_argument('--schemes', metavar='"cubic bbr vegas"',
                       help='Space-separated list of CC schemes to test')

    args = parser.parse_args()

    try:
        run_cc_schemes(args)
    except Exception as e:
        sys.stderr.write(f"[ERROR] Exception caught: {e}\n")
        cleanup()
        raise
    else:
        sys.stderr.write("✅ All tests finished cleanly\n")


if __name__ == '__main__':
    main()

