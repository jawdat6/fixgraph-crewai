import os
from typing import Optional, Type
from pydantic import BaseModel, Field
import requests

try:
    from crewai.tools import BaseTool
except ImportError:
    from crewai_tools import BaseTool


class FixGraphSearchInput(BaseModel):
    query: str = Field(description="Error message or technical problem to search for fixes")


class FixGraphTool(BaseTool):
    name: str = "fixgraph_search"
    description: str = (
        "Search FixGraph for engineering fixes and solutions. "
        "Use this when you encounter an error or technical problem. "
        "Returns verified fixes with root cause analysis and step-by-step solutions."
    )
    args_schema: Type[BaseModel] = FixGraphSearchInput
    api_key: Optional[str] = None
    base_url: str = "https://fixgraph.netlify.app"
    limit: int = 3

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, limit: int = 3):
        super().__init__()
        self.api_key = api_key or os.getenv("FIXGRAPH_API_KEY", "")
        if base_url:
            self.base_url = base_url
        self.limit = limit

    def _run(self, query: str) -> str:
        headers = {
            "Accept": "application/json",
            "User-Agent": "fixgraph-crewai/0.1.0",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        params = {"q": query, "limit": self.limit}
        url = f"{self.base_url}/api/issues/search"

        try:
            res = requests.get(url, params=params, headers=headers, timeout=10)
            res.raise_for_status()
            data = res.json()
        except Exception as e:
            return f"FixGraph search failed: {e}"

        issues = data.get("items") or data.get("results") or data.get("issues") or data.get("data") or []

        if not issues:
            return f"No fixes found for: {query}"

        parts = []
        for i, issue in enumerate(issues):
            lines = [f"## Fix {i + 1}: {issue.get('title', 'Untitled')}"]
            score = issue.get("trust_score")
            if score is not None:
                lines.append(f"Trust: {score}%")
            rc = issue.get("root_cause") or issue.get("rootCause")
            if rc:
                lines.append(f"\nRoot Cause: {rc}")
            steps = issue.get("steps") or issue.get("fixSteps") or []
            if steps:
                lines.append("\nSteps:")
                for j, step in enumerate(steps):
                    if isinstance(step, str):
                        lines.append(f"  {j + 1}. {step}")
                    else:
                        title = f"{step.get('title', '')}: " if step.get("title") else ""
                        lines.append(f"  {j + 1}. {title}{step.get('description', '')}")
                        if step.get("code"):
                            lines.append(f"```\n{step['code']}\n```")
            slug = issue.get("slug") or issue.get("id")
            if slug:
                lines.append(f"\nURL: {self.base_url}/issues/{slug}")
            parts.append("\n".join(lines))

        return "\n\n---\n\n".join(parts)
