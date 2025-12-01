# HawkSightAI Project

HawkSightAI is an end‑to‑end demonstration of an autonomous data governance platform built on the Google Agent Development Kit (ADK). It shows how a multi‑agent architecture can profile data, detect schema drift and anomalies, identify compliance issues, remediate duplicate records and other errors, and compile a governance report. The code in this repository is organised into logical modules for agents, tools, configuration, and data generation.

<p align="center">
    <img width="518" height="357" alt="image" src="https://github.com/user-attachments/assets/c2afdd0b-bcdc-4e8b-aba6-8cae86dfc861" />
</p>

---

## Project Structure

```
hawksightai_project/
├── README.md                # Documentation
├── config.json              # Configuration for data paths, storage, and LLM
├── hawksight_ai.py          # Main entry point to run the workflow
├── agents/
│   ├── __init__.py
│   └── agents.py            # Agent definitions and orchestrator
├── tools/
│   ├── __init__.py
│   └── data_tools.py        # Profiling, anomaly detection, compliance checks, etc.
└── data/
    └── generate_data.py     # Script to generate synthetic datasets
```

---

### `config.json`

This file contains configuration fields used during the run. If you are connecting to cloud storage, update the placeholders.
For local testing, only the `data` and `llm` sections matter.

Example:

```json
{
  "aws": {
    "access_key_id": "YOUR_AWS_ACCESS_KEY_ID",
    "secret_access_key": "YOUR_AWS_SECRET_ACCESS_KEY",
    "region": "ap-south-1",
    "s3_bucket": "your-s3-bucket"
  },
  "azure": {
    "connection_string": "YOUR_AZURE_STORAGE_CONNECTION_STRING",
    "container": "your-container"
  },
  "gcp": {
    "project_id": "your-gcp-project-id",
    "credentials_file": "path/to/service-account.json",
    "bucket": "your-gcs-bucket"
  },
  "data": {
    "baseline_file": "data/transactions_baseline.csv",
    "current_file": "data/transactions_current.csv"
  },
  "llm": {
    "google_api_key": "YOUR_GOOGLE_API_KEY",
    "model_name": "gemini-2.0-flash"
  }
}
```

> Do not commit real credentials.

The demo does not directly connect to cloud buckets; instead it reads local files. You can extend the data loading in hawksight_ai.py to fetch from cloud storage using these credentials if desired. The llm section holds settings for the Gemini‑powered agents. If you provide a valid google_api_key from Google AI Studio and specify a model_name (for example gemini-2.0-flash or gemini-2.5-pro-preview-03-25), the orchestrator will attempt to instantiate LLM agents via the ADK. When the ADK is unavailable or you omit the key, the demo gracefully falls back to deterministic agents that do not invoke an LLM.

---

### `hawksight_ai.py`

This script serves as the entry point for the demo.  It
performs the following steps:

1. Loads configuration from `config.json`.
2. Generates synthetic datasets in the `data` directory if they
   don’t already exist.
3. Profiles the baseline dataset using a custom tool.
4. Instantiates an ADK session and preloads the baseline profile
   into session state (if ADK is installed).
5. Runs the orchestrator (`EagleAgent`) to profile the current
   dataset, detect anomalies and drift, identify compliance
   issues, perform deduplication, and generate a governance
   report.
6. Prints the path to the report.

If the ADK is not installed the script gracefully informs you
and still creates the synthetic datasets so you can run the
tool functions manually.

### `agents/agents.py`

Contains definitions for specialized agents derived from
`BaseAgent` and a helper function to build the orchestrator.
These agents correspond to the roles defined in the HawkSightAI
architecture:
- Profiling agent
- Drift/anomaly detection agent
- Compliance agent
- Repair agent
- Report agent
The `create_eagle_agent()` function constructs a sequential
agent that runs these sub‑agents in order.

### `tools/data_tools.py`

Implements all custom functions used by the agents.  Functions
include:

- `create_datasets(base_dir, n)` – generate synthetic baseline and
  current CSV datasets for testing.
- `profile_data(path)` – build a schema and statistics profile.
- `detect_anomalies_and_drift(current_path, baseline_profile)` –
  compare the current data against the baseline profile to find
  new/removed columns, mean shifts, and duplicates.
- `detect_pii(path)` – flag unmasked email addresses.
- `sync_tables(path)` – remove duplicate rows and write a
  cleaned dataset.
- `generate_lineage_graph()` – placeholder that returns a
  description of lineage relationships.
- `save_governance_report(report, output_dir)` – write a JSON
  governance report to disk.

### `data/generate_data.py`

Convenience script for generating synthetic datasets.  You can
run this script directly to refresh the baseline and current
files.  It simply wraps `create_datasets()` from the tools
module.

## Setup Instructions

1. **Create environment & install dependencies**

   ```bash
   python -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
   pip install pandas numpy
   pip install google-python-agent-sdk
   pip install google-generativeai   # Optional: only needed for Gemini agents
   ```

2. **Update configuration**

   Edit `config.json` with file paths or credentials as needed.

3. **Generate demo data (optional)**

   ```bash
   python data/generate_data.py
   ```

4. **Run HawkSightAI**

   ```bash
   python hawksight_ai.py
   ```

Once executed, the system creates:

* A governance JSON report
* Detection summary
* A cleaned dataset when duplicates were found

---

## Notes

This version is a foundation. Future additions may include:

* Advanced anomaly scoring
* Custom rule engines
* Ticketing or messaging notifications
* Lineage graph visualization
* Integration with enterprise data platforms

---

<p align="center">Crafted with Love, purpose, and a hawk’s eye — <strong>Purvansh Singh</strong></p>

---
