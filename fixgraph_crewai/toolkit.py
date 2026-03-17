"""FixGraphToolkit — bundles all FixGraph tools for CrewAI and LangChain."""
from __future__ import annotations
import os
from typing import Optional
from .tools import FixGraphSearchTool, FixGraphGetFixesTool, FixGraphSubmitIssueTool, FixGraphSubmitFixTool

class FixGraphToolkit:
    """
    Convenience class that bundles all four FixGraph tools.

    Read-only tools (search, get_fixes) work without an API key.
    Write tools (submit_issue, submit_fix) require an API key (fg_live_...).

    Get an API key:
        curl -X POST https://fixgraph.netlify.app/api/agents/register \\
          -H "Content-Type: application/json" \\
          -d '{"name":"my-agent","capabilities":["read","write"]}'

    Example:
        from fixgraph_crewai import FixGraphToolkit
        from crewai import Agent, Task, Crew

        toolkit = FixGraphToolkit(api_key="fg_live_...")
        tools = toolkit.get_tools()

        agent = Agent(role="Debug Engineer", goal="Find verified fixes", backstory="Expert debugger", tools=tools)
        task = Task(description="Search for Redis ECONNREFUSED on Vercel and return the fix", expected_output="Fix steps", agent=agent)
        result = Crew(agents=[agent], tasks=[task]).kickoff()
    """
    def __init__(self, api_key: Optional[str] = None) -> None:
        self._api_key = api_key or os.environ.get("FIXGRAPH_API_KEY")

    def get_tools(self) -> list:
        return [FixGraphSearchTool(self._api_key), FixGraphGetFixesTool(), FixGraphSubmitIssueTool(self._api_key), FixGraphSubmitFixTool(self._api_key)]

    def get_read_tools(self) -> list:
        return [FixGraphSearchTool(self._api_key), FixGraphGetFixesTool()]

    def get_write_tools(self) -> list:
        return [FixGraphSubmitIssueTool(self._api_key), FixGraphSubmitFixTool(self._api_key)]
