# HawkSightAI Project

HawkSightAI is an end‑to‑end demonstration of an autonomous data
governance platform built on the Google Agent Development Kit (ADK).
It shows how a multi‑agent architecture can profile data,
detect schema drift and anomalies, identify compliance issues,
remediate duplicate records and other errors, and compile a
governance report.  The code in this repository is organised
into logical modules for agents, tools, configuration, and data
generation.

<p align="center">
    <img width="518" height="357" alt="image" src="https://github.com/user-attachments/assets/c2afdd0b-bcdc-4e8b-aba6-8cae86dfc861" />
</p>


## Project Structure

```
hawksightai_project/
├── README.md                # This file
├── config.json              # Configuration placeholders (credentials and data paths)
├── hawksight_ai.py          # Main entry point to run the demo
├── agents/
│   ├── __init__.py
│   └── agents.py            # Definitions of ADK agents and orchestrator
├── tools/
│   ├── __init__.py
│   └── data_tools.py        # Profiling, anomaly detection, PII detection, etc.
└── data/
    └── generate_data.py     # Script to generate synthetic datasets for demo
```

### `config.json`

This JSON file holds credentials and paths used by the demo.  **It
should never be committed with real secrets.**  Before running
the demo you must update the placeholders with valid credentials
for your own AWS S3, Azure Blob Storage, or Google Cloud Storage
environments.  The `data` section points to the baseline and
current files used for profiling and anomaly detection.  For
example:

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

Update the fields to point to your own resources.  The demo does
not directly connect to cloud buckets; instead it reads local
files.  You can extend the data loading in `hawksight_ai.py` to
fetch from cloud storage using these credentials if desired.

The `llm` section holds settings for the Gemini‑powered agents.  If
you provide a valid `google_api_key` from Google AI Studio and
specify a `model_name` (for example `gemini-2.0-flash` or
`gemini-2.5-pro-preview-03-25`), the orchestrator will attempt to
instantiate LLM agents via the ADK.  When the ADK is unavailable or
you omit the key, the demo gracefully falls back to deterministic
agents that do not invoke an LLM.

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
architecture: data profiling, drift and anomaly detection,
compliance checking, data repair, and reporting.  The
`create_eagle_agent()` function constructs a sequential
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

1. **Install dependencies**.  Create a new virtual environment and
   install the required libraries.  At a minimum, you need
   `pandas` and `numpy` for the data tools.  To run the LLM agents,
   you must also install the Google Agent Development Kit (ADK) and
   optionally the Gemini client libraries:

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # or .venv\Scripts\activate on Windows
   # Core libraries
   pip install pandas numpy
   # Install the Python version of the Agent Development Kit
   pip install google-python-agent-sdk
   # (Optional) Install google-generativeai if you plan to call Gemini
   pip install google-generativeai
   ```

   The `google-python-agent-sdk` package installs the ADK.  Without it,
   the orchestrator will fall back to deterministic agents and will
   not call the Gemini LLM.  The optional `google-generativeai` package
   provides the underlying client library used by ADK to communicate
   with Gemini.

2. **Configure secrets**.  Open `config.json` and replace the
   placeholder values with your real AWS, Azure, or GCP
   credentials and bucket/container names.  If you don’t use
   cloud storage you can leave these fields unchanged.  Ensure
   the `data` section points to your baseline and current CSV
   files.

3. **Generate data (optional)**.  To generate synthetic data
   matching the demo scenario, run:

   ```bash
   python data/generate_data.py
   ```

   This will create `transactions_baseline.csv` and
   `transactions_current.csv` under the `data` directory.

4. **Run the demo**.  Execute the main script:

   ```bash
   python hawksight_ai.py
   ```

   The script profiles the baseline, then attempts to run a
   sequential orchestrator.  If ADK and a valid Gemini API key are
   available (see the `llm` section of `config.json`), the
   orchestrator will use LLM agents to reason about the data and
   coordinate tool use.  Otherwise it falls back to deterministic
   agents.  Upon completion it writes a governance report to the
   `data` directory summarizing detected anomalies, compliance
   issues, and the location of the cleaned dataset.

5. **Extend for real data**.  To integrate with real S3, Azure,
   or GCS buckets, modify the data loading in
   `hawksight_ai.py` to read from the respective services using
   the credentials in `config.json`.  For example, you could
   use `boto3` for S3, `azure-storage-blob` for Azure Blob
   Storage, and `google-cloud-storage` for GCS.  After loading
   into pandas DataFrames, pass them to the tools in the same
   way as the local CSV files.

## Notes

- This project is a starting point, we can add
  more sophisticated anomaly detection, compliance policies,
  repair logic, and integration with messaging or ticketing
  systems.

---


<p align="center">Crafted with Love, purpose, and a hawk’s eye — Purvansh Singh</strong></p>
