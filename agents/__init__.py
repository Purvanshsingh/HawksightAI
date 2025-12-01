"""Agent package for HawkSightAI.

This package exposes helper functions and classes for constructing
and running the specialized agents used in the HawkSightAI demo.
Importing the package will automatically import the
`create_eagle_agent` function, which builds the orchestrator.
"""

"""Agent package for HawkSightAI.

This package exposes helper functions and classes for constructing and
running the specialized agents used in the HawkSightAI demo.  Importing
the package will automatically import two helper constructors:

* ``create_eagle_agent`` – builds the deterministic non‑LLM orchestrator.
* ``create_llm_eagle_agent`` – builds the LLM‑powered orchestrator using
  Gemini and the Google Agent Development Kit.

If the Google ADK package is not installed, calls to these functions
will raise a ``RuntimeError`` to signal that the required dependency is
missing.
"""

from .agents import create_eagle_agent, create_llm_eagle_agent  # noqa: F401