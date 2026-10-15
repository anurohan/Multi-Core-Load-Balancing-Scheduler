# Multi-Core Load Balancing Scheduler

A Streamlit project for exploring operating-system scheduling and dynamic workload distribution across multiple simulated CPU cores. The repository contains a simulation engine, a dashboard, visualization/export modules, dependency notes, and an academic project report.

## Intended capabilities

The scheduler engine describes and implements least-loaded-core assignment, work stealing, aging, and FCFS, Round Robin, and priority-based scheduling. The dashboard is designed to show core utilization, process timelines, load balance, and scheduling metrics, and includes CSV/PDF export utilities.

## Technology

- Python 3.9 or later.
- Streamlit for the interactive dashboard.
- Plotly and Altair for charts.
- Pandas and NumPy for tabular and numerical support.
- FPDF2 for PDF report export.

The pinned package versions are listed in the repository file named `Requirements'` (including the trailing apostrophe).

## Setup

Create a virtual environment, activate it, and install the listed packages:

```sh
python -m venv .venv
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
python -m pip install -r "Requirements'"
```

macOS/Linux:

```sh
source .venv/bin/activate
python -m pip install -r "Requirements'"
```

The intended dashboard command is:

```sh
streamlit run app.py
```

## Repository map

- `app.py` — Streamlit dashboard and simulation controls.
- `scheduler.py` — process models and scheduling algorithms.
- `visualizations.py` — Plotly chart helpers.
- `export.py` — CSV and PDF export functions.
- `Reademe..Instruction & working` — existing project setup and usage notes.
- `project report AI generated` — project report.

## Current checkout note

The dashboard imports `utils.scheduler`, `utils.visualizations`, and `utils.export`, but the checked-in modules are currently at the repository root and there is no `utils/` directory. As a result, the listed Streamlit command needs the module paths reconciled before it can run from this checkout. The project report and setup notes describe the intended structure; this README does not claim the current layout has been verified as runnable.