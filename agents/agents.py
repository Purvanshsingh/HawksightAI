"""Specialized agents and orchestrator for HawkSightAI.

This module defines several subclasses of :class:`google.adk.agents.BaseAgent`
that perform data profiling, drift and anomaly detection, compliance
checking, data repair, and reporting.  It also provides a helper
function to create the sequential orchestrator (the "Eagle" agent).

The agents rely on functions defined in ``hawksightai_project.tools.data_tools``.
To use these agents you must have the Google Agent Development Kit
(ADK) installed.  If the ADK cannot be imported the agents will not
be available.
"""

from __future__ import annotations

import datetime
from typing import Any, Dict, List

try:
    # Import the core classes.  LlmAgent may not be available if ADK is not installed.
    from google.adk.agents import BaseAgent, SequentialAgent, LlmAgent
    from google.adk.agents import ParallelAgent  # noqa: F401 imported for completeness
    from pydantic import BaseModel, Field
    ADK_AVAILABLE = True
except ImportError:
    # Define stubs when ADK is unavailable so type hints don't fail.
    class BaseAgent:  # type: ignore
        pass
    class SequentialAgent:  # type: ignore
        pass
    class LlmAgent:  # type: ignore
        pass
    class ParallelAgent:  # type: ignore
        pass
    class BaseModel:  # type: ignore
        pass
    def Field(*args, **kwargs):  # type: ignore
        return None
    ADK_AVAILABLE = False

# Import tools using an absolute import rather than a relative import.
# When this module is executed as part of a standalone script (not as part
# of a package) relative imports using ``..`` will fail because there is no
# parent package.  Absolute imports ensure Python can resolve the modules
# correctly when the project directory is on the sys.path.
from tools.data_tools import (
    profile_data,
    detect_anomalies_and_drift,
    detect_pii,
    sync_tables,
    generate_lineage_graph,
    save_governance_report,
    compile_report,
)


if ADK_AVAILABLE:
    class DataProfilerAgent(BaseAgent):
        """Profile the dataset and store the profile in session state."""
        name: str = "DataProfiler"
        description: str = "Generate statistical and structural profiles for a dataset."

        async def act(self, request: Dict[str, Any], session):
            file_path = request.get("file_path")
            profile = profile_data(file_path)
            session.state["profile"] = profile
            return {"profile": profile}

    class DriftAnomalyAgent(BaseAgent):
        """Compare current data against a baseline profile and report anomalies."""
        name: str = "DriftAnomaly"
        description: str = "Detect schema drift, distribution shifts, and duplicate records."

        async def act(self, request: Dict[str, Any], session):
            file_path = request.get("file_path")
            baseline_profile = session.state.get("baseline_profile")
            anomalies = detect_anomalies_and_drift(file_path, baseline_profile)
            session.state["anomalies"] = anomalies
            return {"anomalies": anomalies}

    class ComplianceAgent(BaseAgent):
        """Check for exposed PII such as unmasked emails."""
        name: str = "Compliance"
        description: str = "Identify PII exposures and policy violations."

        async def act(self, request: Dict[str, Any], session):
            file_path = request.get("file_path")
            issues = detect_pii(file_path)
            session.state["compliance_issues"] = issues
            return {"issues": issues}

    class SyncRepairAgent(BaseAgent):
        """Repair data by removing duplicates and writing a cleaned file."""
        name: str = "SyncRepair"
        description: str = "Remove duplicate rows and align schema."

        async def act(self, request: Dict[str, Any], session):
            file_path = request.get("file_path")
            cleaned_path = sync_tables(file_path)
            session.state["cleaned_path"] = cleaned_path
            return {"cleaned_path": cleaned_path}

    class ReportingAgent(BaseAgent):
        """Compile profiling, anomaly, compliance, and repair results into a report."""
        name: str = "Reporting"
        description: str = "Compile results into a governance report."

        async def act(self, request: Dict[str, Any], session):
            profile = session.state.get("profile")
            anomalies = session.state.get("anomalies")
            issues = session.state.get("compliance_issues")
            cleaned_path = session.state.get("cleaned_path")
            lineage = generate_lineage_graph()
            report = {
                "timestamp": datetime.datetime.utcnow().isoformat(),
                "profile": profile,
                "anomalies": anomalies,
                "compliance_issues": issues,
                "cleaned_path": cleaned_path,
                "lineage": lineage,
            }
            report_path = save_governance_report(report)
            session.state["report_path"] = report_path
            return {"report_path": report_path, "report": report}

    def create_eagle_agent() -> SequentialAgent:
        """Construct the sequential orchestrator (Eagle Agent).

        Returns a :class:`google.adk.agents.SequentialAgent` composed
        of the specialized agents defined above.  If ADK is not
        available this function raises a RuntimeError.
        """
        if not ADK_AVAILABLE:
            raise RuntimeError("Google ADK is not available. Install google-adk to use agents.")
        return SequentialAgent(
            name="EagleAgent",
            description="Master orchestrator that profiles data, detects drift & anomalies, checks compliance, repairs data, and reports.",
            sub_agents=[
                DataProfilerAgent(),
                DriftAnomalyAgent(),
                ComplianceAgent(),
                SyncRepairAgent(),
                ReportingAgent(),
            ],
        )

    # ------------------------------------------------------------------
    # LLM-powered Agents
    # These agents leverage Google ADK's LlmAgent class.  Each agent
    # includes an instruction describing its role and the tools it can
    # invoke.  Output keys are used to persist results in session state.
    class FileInput(BaseModel):
        """Schema for input to agents expecting a file path."""

        file_path: str = Field(..., description="Path to the data file to process")

    def create_llm_eagle_agent(model: str = "gemini-2.0-flash") -> SequentialAgent:
        """Construct a sequential orchestrator composed of LLM agents.

        Args:
            model: Identifier for the Gemini model to use.  Examples include
                ``"gemini-2.0-flash"`` for a fast model or
                ``"gemini-2.5-pro-preview-03-25"`` for more powerful output.

        Returns:
            A SequentialAgent orchestrating all HawkSightAI LLM agents.
        """
        # Data profiler: compute basic statistics and schema.  Save to state['profile']
        data_profiler = LlmAgent(
            model=model,
            name="DataProfilerLLM",
            description="Profiles a dataset by generating statistical and structural metadata.",
            instruction="""
You are a data profiler.  When given a file path, your goal is to
create a profile of the dataset, including row counts, column data types,
missing values, and basic statistics for numeric columns.  Use the
`profile_data` tool to perform the profiling.  Pass the `file_path`
provided by the user directly to the tool.  After calling the tool,
store the resulting profile dict into the session state under the key
`profile`.  Return a short acknowledgement summarizing the number of
columns profiled.
""",
            tools=[profile_data],
            input_schema=FileInput,
            output_key="profile",
        )

        # Drift & anomaly detector: compare current data to baseline profile
        drift_anomaly = LlmAgent(
            model=model,
            name="DriftAnomalyLLM",
            description="Detects schema drift, distribution shifts, and duplicate records by comparing a dataset to a baseline profile.",
            instruction="""
You are a drift and anomaly detection agent.  The baseline
profile has been stored in session state under the key `baseline_profile`.
Use the `detect_anomalies_and_drift` tool to compare the current file
against the baseline.  Call the tool with two arguments: the current
file path provided by the user and the baseline profile loaded from
session state as {baseline_profile}.  Save the list of anomaly
descriptions returned by the tool into the session state under
`anomalies`.  Summarize how many anomalies were found in your final
response.
""",
            tools=[detect_anomalies_and_drift],
            input_schema=FileInput,
            output_key="anomalies",
        )

        # Compliance checker: scan for exposed PII
        compliance = LlmAgent(
            model=model,
            name="ComplianceLLM",
            description="Scans the dataset for unmasked email addresses and other PII violations.",
            instruction="""
You are a compliance agent responsible for detecting PII exposures in the
dataset.  Use the `detect_pii` tool on the provided file path to
identify any unmasked or improperly stored email addresses.  Save the
list of issues into session state under the key `compliance_issues`.
Respond with a brief summary of the findings.
""",
            tools=[detect_pii],
            input_schema=FileInput,
            output_key="compliance_issues",
        )

        # Sync & repair: remove duplicates and align schema
        sync_repair = LlmAgent(
            model=model,
            name="SyncRepairLLM",
            description="Cleans the current dataset by removing duplicate rows and aligning the schema.",
            instruction="""
You are a repair agent tasked with cleaning the current dataset.  Use
the `sync_tables` tool on the provided file path to remove duplicate
rows and output a cleaned CSV file.  Store the path of the cleaned
file in session state under `cleaned_path`.  Respond with the path of
the cleaned file.
""",
            tools=[sync_tables],
            input_schema=FileInput,
            output_key="cleaned_path",
        )

        # Reporting: compile results and write report
        report_agent = LlmAgent(
            model=model,
            name="ReportingLLM",
            description="Compiles profiling, anomaly, compliance, and repair results into a governance report.",
            instruction="""
You are a reporting agent that prepares a governance report using the
results from previous steps.  First, use the `generate_lineage_graph` tool
to obtain the data lineage description; store the result in a variable `lineage`.
Next, use the `compile_report` tool to combine the following inputs:
profile={profile}, anomalies={anomalies}, compliance_issues={compliance_issues},
cleaned_path={cleaned_path}, and lineage=lineage.  Assign the returned report
dictionary to a variable `report`.  Finally, call the `save_governance_report` tool
with the `report` dictionary as its only argument to persist the report to disk.
Save the file path returned by `save_governance_report` to session state under
`report_path`.  Respond with a message indicating that the report has been
generated and provide the path.
""",
            tools=[generate_lineage_graph, compile_report, save_governance_report],
            input_schema=FileInput,
            output_key="report_path",
        )

        # Compose the sequential orchestrator
        return SequentialAgent(
            name="EagleAgentLLM",
            description="Sequential orchestrator that profiles data, detects drift & anomalies, checks compliance, cleans data, and generates a governance report.",
            sub_agents=[
                data_profiler,
                drift_anomaly,
                compliance,
                sync_repair,
                report_agent,
            ],
        )
else:
    # Provide a stub create_eagle_agent that always raises to inform the caller.
    def create_eagle_agent() -> SequentialAgent:
        raise RuntimeError("Google ADK is not available. Install google-adk to use agents.")

    # Provide a stub for the LLM orchestrator.  When ADK is unavailable
    # this function will raise immediately to signal that LLM agents
    # cannot be constructed.
    def create_llm_eagle_agent(model: str = "gemini-2.0-flash") -> SequentialAgent:  # type: ignore[no-redef]
        raise RuntimeError("Google ADK is not available. Install google-adk to use LLM agents.")
