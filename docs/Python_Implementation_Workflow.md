# Comprehensive Python Implementation Workflow: Vehicle Service Center Hybrid Simulation

This document outlines the architecture, setup, and execution workflow used to implement the **OptiBay Simulator**, integrating Agent-Based Simulation (ABS) for customer behavior and Discrete Event Simulation (DES) for service operations.

## Phase 1: Environment Setup and Architecture Preparation

### 1.1 Technical Stack & Dependencies
The simulation heavily leverages modern Python scientific libraries for high performance and reliable distribution modeling:
* **Simulation Core:** `simpy` (Handles the DES chronological event loop and bay resources).
* **Data Processing:** `pandas`, `numpy`.
* **Statistical Analysis (Distributions & Validation):** `scipy` (Specifically `scipy.stats` for mapping empirical constraints to distributions).
* **Visualization & UI Analytics:** `matplotlib`, `seaborn`, `streamlit` (For rich, interactive dashboards).

### 1.2 Optimized Project Structure
The project follows clean, object-oriented modular patterns:
```
vso-project/
│
├── src/
│   ├── __init__.py        # Defines src as a module
│   ├── config.py          # System constraints, time limits, and bay limits
│   ├── agents.py          # Customer ABS (personality, behavior models)
│   ├── environment.py     # DES system handling simpy resources
│   ├── simulation.py      # Main execution loop syncing agents to the environment
│   └── analysis.py        # Log processing, metrics calculation, and chart generation
│
├── outputs/               # Auto-generated reports, PNG charts, and CSV logs
├── docs/                  # Detailed architectural documentation
├── run.py                 # Terminal/CLI runner for headless simulations
└── app.py                 # Interactive Streamlit Web UI
```

---

## Phase 2: Agent-Based Simulation (ABS) - Customer Behavior Modeling

Each customer is treated as an autonomous `CustomerAgent` whose decisions depend entirely on their psychological traits.

### 2.1 Class Design (`agents.py`):
* **Personality Types:** Conservative, Steady, or Aggressive (Assigned via random probabilities reflecting real-world datasets).
* **Emotional State:** Positive, Neutral, Negative, Unstable (Changes dynamically based on wait time).
* **Patience Threshold:** Time limit before they abandon the queue, heavily influenced by Personality and modified by Emotion.

### 2.2 Decision Rules (Behaviors):
* **Balking (`decide_balk`):** Action evaluated *upon arrival*. Concurrently checks the physical DES queue length. If it exceeds a personality-based threshold, the customer refuses to enter and leaves immediately.
* **Reneging (`reneging_timer`):** Action evaluated *while waiting*. Continuously checks elapsed wait time against the dynamic `Patience Threshold`. If exceeded, triggers an event interrupt prompting the agent to exit the facility.

---

## Phase 3: Discrete Event Simulation (DES) - Physical Operations Modeling

The physical service center handles the chronological vehicle flow in `environment.py` using `simpy.Resource`.

### 3.1 Facility Queues:
1. **Inspection Bay:** First-contact location to determine the severity of repair.
2. **General Repair Bays:** Handles heavy-duty and complex service workflows. 
3. **Express Repair Bays:** Handles fast turnaround services, bypassing the general bottleneck.

---

## Phase 4: Hybrid Integration (The "Human-in-the-Loop")

This phase defines how the psychological ABS interacts with the physical DES within `simulation.py`.

### 4.1 Process Synchronization
1. The master simulation loop generates regular customer arrivals (accelerated during time-of-day rush hours dynamically coded in `config.py`).
2. `car = env.process(service_flow(env, customer, resources))` creates a DES thread for the new arrival.
3. Simultaneously, an ABS monitor thread `env.process(customer.reneging_timer(env))` is attached to that specific customer.
4. If the DES acquires a bay resource *before* the ABS patience timer runs out, the timer is safely terminated (`Got Served`).
5. If the ABS timer executes fully first, it injects a `simpy.Interrupt` into the DES thread, immediately cancelling resource requests and logging the event as **"Reneged."**

---

## Phase 5: Result Analysis and Visualization

When the configured limits are met (`SIMULATION_TIME`), the engine hands the raw chronological logs to `analysis.py`. 

### 5.1 Analytics Pipeline
1. **DataFrame Generation:** `pandas` converts raw logs into an analyzable table.
2. **Key Performance Indicators (KPIs):** Calculates Service Success Rate vs. Asset Abandonment Rates (Balk/Renege).
3. **Distribution Tracking:** Traces timestamps from "Arrival" to "Service Start" to calculate exact wait-times per customer.
4. **Visual Processing:** Generates pie charts, histogram queue plots, and wait-time box plots utilizing `seaborn` color palettes and saves PNGs natively to the `outputs/` folder.
