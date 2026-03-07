# Vehicle Service Center Hybrid Simulation (ABS + DES)

## Overview
This project is a standalone Python simulation model designed to analyze and optimize the operations of a heavy-duty Vehicle Service Center. 

It pioneers a **Hybrid Modeling Methodology**, combining:
1. **Discrete Event Simulation (DES):** Models the physical service workflows (Arrival -> Inspection -> General/Express Repair -> Departure) using `simpy`. It focuses on bay utilization and technical bottlenecks.
2. **Agent-Based Simulation (ABS):** Models the psychological and behavioral patterns of customers. Customers are treated as autonomous agents with assigned personalities (Conservative, Steady, Aggressive) and dynamic emotional states (Positive, Negative, Unstable).

### Key Behavioral Features
* **Balking:** Customers may refuse to join a queue upon arrival if it exceeds their psychological tolerance threshold.
* **Reneging:** Customers waiting in queues possess a dynamic "patience timer." If their wait time exceeds their patience (which degrades if their emotion turns negative), they will abandon the service center.

---

## Project Structure
```
d:\vso-project\
│
├── src/
│   ├── config.py         # Global simulation parameters and distributions
│   ├── agents.py         # CustomerAgent class evaluating patience and emotions (ABS)
│   ├── environment.py    # ServiceCenter class defining physical resources (DES)
│   ├── simulation.py     # Main processes combining ABS logic with DES queues
│   └── analysis.py       # Metrics calculation and matplotlib/seaborn visualizations
│
├── outputs/              # Directory where generated CSV logs and PNG charts are saved
├── requirements.txt      # Python dependencies
├── run.py                # Command Line Interface runner
└── app.py                # (Upcoming) Interactive Web Dashboard
```

---

## Installation

1. Ensure Python 3.9+ is installed.
2. Clone or navigate to the project directory:
```bash
cd d:\vso-project
```
3. Install the required libraries:
```bash
pip install -r requirements.txt
```
*(Requires `simpy`, `pandas`, `numpy`, `matplotlib`, `seaborn`)*

---

## Usage (Command Line Interface)

You can run the simulation entirely from the terminal. The `run.py` script accepts arguments to override the default configuration for rapid testing.

**Basic Run:**
```bash
python run.py
```

**Custom Parameter Run:**
```bash
python run.py --time 1200 --bays 8 --express 2
```
*Options:*
* `--time`: Total simulation time in minutes (Default: 600).
* `--bays`: Number of General Repair Bays (Default: 5).
* `--express`: Number of Express Repair Bays (Default: 1).

### Expected Outputs
Upon completion, the script generates:
1. Console summary of Total Customers, Successfully Serviced %, Balked %, and Reneged %.
2. `outputs/sim_logs.csv`: The raw chronological event log of every customer.
3. `outputs/*.png`: Graphical charts visualizing queue traffic load, wait time distributions, and final customer outcomes.

---

## Future Enhancements
* **Interactive UI:** A Web Dashboard for real-time parameter tweaking and visualization viewing.
* **Apriori Factor Ranking:** Integration of expert-driven analytical weights to dynamically configure Service Time parameters and technician workforce scheduling.
