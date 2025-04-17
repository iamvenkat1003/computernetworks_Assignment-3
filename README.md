README.md
Pantheon Congestion Control Experiments
Computer Networks – Programming Assignment 3 (Spring 2025)

This repository contains code, logs, and analysis related to congestion control protocol experiments conducted using the Pantheon framework and Mahimahi network emulator. The goal of this assignment is to evaluate multiple congestion control (CC) schemes under varied network conditions, and to analyze their performance based on metrics like throughput, RTT, and packet loss.

This document outlines the setup process, challenges encountered, debugging methods, and the final procedure used to run experiments and collect results. All work has been done entirely within this workspace and is based on the requirements listed in the assignment prompt.

Overview
Pantheon is an open-source framework that standardizes congestion control evaluation by integrating multiple CC algorithms with Mahimahi, a network emulation toolkit. It is no longer maintained, but the open-source code still supports practical research and academic experimentation.

The experiments performed here involve three different congestion control protocols:

Cubic
BBR
Vegas

Two different network profiles are emulated:
Low-latency, high-bandwidth (50 Mbps, 10 ms RTT)
High-latency, constrained-bandwidth (1 Mbps, 200 ms RTT)

Each combination of protocol and network profile is tested independently for a duration of at least 60 seconds using trace-based emulation. All logs are collected and stored for post-experiment analysis.

Environment Setup
This entire project was executed within an Ubuntu 24.04 virtual machine running under UTM on macOS. The virtual machine setup included:
Installation of Ubuntu via ISO using UTM
Installation of VSCode for in-VM development
Download and configuration of the Pantheon repository
Setup of Python 2.7 (required for Pantheon scripts)
Setup of Python 3.x for new scripting and visualization
Installation of Mahimahi and all required dependencies

To get Pantheon working, the following steps were performed:
Clone the Pantheon GitHub repository using: git clone https://github.com/StanfordSNR/pantheon.git

Install dependencies including Mahimahi, Apache2, dnsmasq, libssl-dev, and libprotobuf-dev.

Fix Mahimahi compatibility issues on Ubuntu 24.04 by installing packages like:

protobuf-compiler

libpangocairo

libxcb-present

libxcb1-dev

Resolve Pantheon build errors by manually configuring and installing each missing library.

Debugging Process
Throughout the development of this assignment, various errors and issues were encountered. Below is a log of key debugging sessions and their resolutions:

1. Missing run_test.py
Pantheon’s documentation referenced run_test.py, which does not exist in the modern fork. A custom script was developed (runtests.py) to automate the testing of multiple schemes.

2. Submodule Issues
The command git submodule update --init --recursive was used to fetch third-party dependencies. The proto-quic submodule caused hang-ups and was intentionally removed via:

git submodule deinit third_party/proto-quic
rm -rf .git/modules/third_party/proto-quic
rm -rf third_party/proto-quic

3. Python Environment Conflicts
Pantheon scripts were dependent on Python 2.7, while plotting and orchestration scripts were written in Python 3. Separate environments were maintained, with python symlinked to python2.7 for legacy compatibility, and python3 used for analysis.

4. Missing Python Modules
Packages like yaml, pyyaml, and matplotlib were missing in the Python 2.7 environment and had to be installed manually using pip. For example:
python -m pip install pyyaml
python -m pip install matplotlib

5. Vegas/BBR Not Enabled
BBR and Vegas were not initially available. They were enabled using:

sudo modprobe tcp_bbr
sudo sysctl -w net.ipv4.tcp_congestion_control=bbr

Vegas required:
sudo modprobe tcp_vegas

6. Mahimahi Failures
When running Mahimahi, the following command fixed a critical IP forwarding issue:
sudo sysctl -w net.ipv4.ip_forward=1


Other issues like shutdown failed: transport endpoint is not connected were harmless and ignored.

Experiment Design (Part B)
This section covers the design and execution of experiments as described in Part B of the assignment.

Protocols Compared
Cubic (default in Linux)

BBR (modern, RTT-resilient)

Vegas (delay-based)

Network Profiles Used
Low-latency High-bandwidth

Trace file: emulated/const50.trace

Simulates 50 Mbps bandwidth and 10 ms RTT

High-latency Constrained-bandwidth

Trace file: emulated/const1.trace

Simulates 1 Mbps bandwidth and 200 ms RTT

These trace files are provided in the emulated/ directory of Pantheon and are compatible with Mahimahi.

Logging & Output
Each experiment was executed for 60 seconds. Output was collected in the following format:

results/
├── cubic_low.log
├── cubic_high.log
├── bbr_low.log
├── bbr_high.log
├── vegas_low.log
├── vegas_high.log

Logs contain standard output from Pantheon scripts, including:
iperf statistics
Mahimahi queueing info
Bandwidth, RTT, and loss rate data
Congestion window behavior

Running the Experiments
To replicate the experiments on a clean machine, follow these steps:
Ensure all dependencies are installed (Pantheon, Mahimahi, Python 2.7).
Enable required congestion control modules (bbr, vegas).

In the Pantheon root directory, run:
python3 analysis.py

This script runs all 6 combinations of CC schemes × network profiles and stores results in the results/ directory.
You can modify runtests.py to add more protocols or customize runtime durations.


Final Thoughts
This project required considerable debugging, compatibility fixes, and automation to match the assignment requirements using a now-deprecated codebase. Despite these limitations, all parts of Part B were successfully completed, and the results were collected for Part C analysis.

The provided code, logs, and instructions should allow full reproducibility of the tests on any Linux machine or VM, as long as basic kernel features and packages are available.

For further extension:
You may add more CC schemes like Copa or Vivace
Replace trace files with custom Mahimahi traces
Visualize results using matplotlib and pandas
