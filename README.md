# Vehicle Service Center: Hybrid Simulation Platform

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![SimPy](https://img.shields.io/badge/SimPy-Simulation-green.svg)](https://simpy.readthedocs.io/en/latest/)
[![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-red.svg)](https://streamlit.io/)

A modern, standalone simulation platform evaluating operational efficiencies in a Heavy-Duty Vehicle Service Center using a hybrid modeling approach.

***

## 📖 Comprehensive Documentation
Detailed explanations of the codebase, mathematical models, and Agent logic have been moved to the `docs/` directory for cleaner project navigation.
* [**System Architecture & Python Workflow**](./docs/Python_Implementation_Workflow.md)
* [**Original Master Documentation (Prior to refactor)**](./docs/README.md)

***

## 🚀 Quick Start Guide

### 1. Installation
Ensure you have cloned the repository and built the environment:
```bash
# It is recommended to use a virtual environment
python -m venv .venv
source .venv/scripts/activate

pip install -r requirements.txt
```

### 2. Run the Web Dashboard *(Recommended)*
We have built a highly interactive front-end using Streamlit which allows you to adjust Simulation Parameters (Sim Time, Bay Capacities) on the fly and immediately view the generated Matplotlib/Seaborn distribution graphs and outcomes.
```bash
streamlit run app.py
```

### 3. Run the Command Line Interface (CLI)
If you prefer running headless simulations for batch analysis:
```bash
# Run with default configuration
python run.py

# Run with customized variables and verbose diagnostic logging
python run.py --time 1440 --bays 10 --express 2 --verbose
```
Outputs from the CLI run are saved to the `outputs/` directory dynamically.

***

## ✨ Advanced Features Added
* **Time-of-Day Traffic Load:** The generic Poisson arrival rates have been upgraded. The system now recognizes "Rush Hours" (e.g., 08:00–10:00 AM) and compresses arrival intervals realistically to stress-test the `simpy` queueing models.
* **Standardized Logging Integration:** The system discards primitive print statements in favor of Python's standardized `logging` library, allowing `--verbose` debugging traces on demand.
