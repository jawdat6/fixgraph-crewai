"""FixGraph CrewAI tools — 4 tools: search, get_fixes, submit_issue, submit_fix."""
from __future__ import annotations
import json, os
from typing import Any, Optional, Type
import requests
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

BASE_URL = "https://fixgraph.netlify.app"

def _get(path: str, params: Optional[dict] = None) -> dict:
    r = requests.get(f"{BASE_URL}{path}", params=params, headers={"User-Agent": "fixgraph-crewai/1.0.0"}, timeout=15)
    r.raise_for_status(); return r.json()

def _post(path: str, payload: dict, api_key: str) -> dict:
    r = requests.post(f"{BASE_URL}{path}", json=payload, headers={"Authorization": f"Bearer {api_key}", "User-Agent": "fixgraph-crewai/1.0.0"}, timeout=15)
    r.raise_for_status(); return r.json()

# ── Search ────────────────────────────────────────────────────────────────────
class _SearchIn(BaseModel):
    query: str = Field(description="Error message or problem description to search for")
    page_size: int = Field(default=5, description="Results per page (max 50)")

class FixGraphSearchTool(BaseTool):
    name: str = "FixGraph Search"
    description: str = "Search FixGraph for verified engineering fixes by error message or description. Returns ranked issues with IDs, titles, and confidence scores."
    args_schema: Type[BaseModel] = _SearchIn
    api_key: Optional[str] = Field(default=None, exclude=True)

    def __init__(self, api_key: Optional[str] = None, **kw: Any) -> None:
        super().__init__(**kw)
        self.api_key = api_key or os.environ.get("FIXGRAPH_API_KEY")

    def _run(self, query: str, page_size: int = 5) -> str:
        try:
            data = _get("/api/issues/search", {"q": query, "pageSize": page_size})
            items = data.get("items") or data.get("results") or data.get("issues") or []
            if not items:
                return json.dumps({"status": "no_results", "query": query})
            return json.dumps({"status": "ok", "total": data.get("total", len(items)), "items": [{"id": it["id"], "slug": it.get("slug",""), "title": it["title"], "confidence_score": it.get("confidence_score", 0), "fix_count": it.get("_count", {}).get("fixes", 0) or len(it.get("fixes", []))} for it in items]})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

# ── Get Fixes ─────────────────────────────────────────────────────────────────
class _GetFixesIn(BaseModel):
    issue_id: str = Field(description="FixGraph issue ID or slug from a search result")

class FixGraphGetFixesTool(BaseTool):
    name: str = "FixGraph Get Fixes"
    description: str = "Get the canonical verified fix for a FixGraph issue. Input: issue ID or slug. Returns step-by-step instructions, root cause, trust score, risk level."
    args_schema: Type[BaseModel] = _GetFixesIn

    def __init__(self, api_key: Optional[str] = None, **kw: Any) -> None:
        super().__init__(**kw)

    def _run(self, issue_id: str) -> str:
        try:
            data = _get(f"/api/issues/{issue_id}/canonical-fix")
            fix = data.get("fix")
            if not fix:
                return json.dumps({"status": "no_fix", "issue_id": issue_id})
            return json.dumps({"status": "ok", "issue_id": data.get("issue_id", issue_id), "fix": {"id": fix["id"], "title": fix["title"], "root_cause": fix["root_cause"], "trust_score": fix.get("trust_score", 0), "risk_level": fix.get("risk_level", "low"), "steps": [{"order": s["order"], "title": s["title"], "description": s["description"], **({"code": s["code"], "code_language": s.get("codeLanguage")} if s.get("code") else {})} for s in fix.get("steps", [])]}})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

# ── Submit Issue ──────────────────────────────────────────────────────────────
class _SubmitIssueIn(BaseModel):
    title: str = Field(description="Issue title (10-200 chars)")
    problem_statement: str = Field(description="Full description (20-5000 chars)")
    error_text: Optional[str] = Field(default=None, description="Exact error or stack trace")
    category_slug: Optional[str] = Field(default=None, description="Category slug, e.g. 'databases'")
    vendor_slug: Optional[str] = Field(default=None, description="Vendor slug, e.g. 'vercel'")
    tags: Optional[list[str]] = Field(default=None, description="Up to 10 tags")

class FixGraphSubmitIssueTool(BaseTool):
    name: str = "FixGraph Submit Issue"
    description: str = "Submit a new engineering issue to FixGraph. Requires API key (fg_live_...). Returns created issue ID."
    args_schema: Type[BaseModel] = _SubmitIssueIn
    api_key: Optional[str] = Field(default=None, exclude=True)

    def __init__(self, api_key: Optional[str] = None, **kw: Any) -> None:
        super().__init__(**kw)
        self.api_key = api_key or os.environ.get("FIXGRAPH_API_KEY")

    def _run(self, title: str, problem_statement: str, error_text: Optional[str] = None, category_slug: Optional[str] = None, vendor_slug: Optional[str] = None, tags: Optional[list] = None) -> str:
        if not self.api_key:
            return json.dumps({"status": "error", "message": "API key required. Set FIXGRAPH_API_KEY or pass api_key."})
        payload: dict = {"title": title, "problem_statement": problem_statement}
        if error_text: payload["error_text"] = error_text
        if category_slug: payload["category_slug"] = category_slug
        if vendor_slug: payload["vendor_slug"] = vendor_slug
        if tags: payload["tags"] = tags
        try:
            r = _post("/api/issues", payload, self.api_key)
            return json.dumps({"status": "created", "id": r["id"], "slug": r.get("slug",""), "message": f"Issue created with ID '{r['id']}'"})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

# ── Submit Fix ────────────────────────────────────────────────────────────────
class _Step(BaseModel):
    order: int; title: str; description: str
    code: Optional[str] = None; code_language: Optional[str] = None

class _SubmitFixIn(BaseModel):
    issue_id: str = Field(description="FixGraph issue ID")
    title: str = Field(description="Fix title (5-200 chars)")
    root_cause: str = Field(description="Root cause explanation (10-2000 chars)")
    steps: list[_Step] = Field(description="Ordered fix steps")
    validation: Optional[str] = Field(default=None)
    risk_level: str = Field(default="low", description="low/medium/high/critical")

class FixGraphSubmitFixTool(BaseTool):
    name: str = "FixGraph Submit Fix"
    description: str = "Submit a fix for a FixGraph issue. Requires API key (fg_live_...). Each step needs order, title, description. Returns created fix ID."
    args_schema: Type[BaseModel] = _SubmitFixIn
    api_key: Optional[str] = Field(default=None, exclude=True)

    def __init__(self, api_key: Optional[str] = None, **kw: Any) -> None:
        super().__init__(**kw)
        self.api_key = api_key or os.environ.get("FIXGRAPH_API_KEY")

    def _run(self, issue_id: str, title: str, root_cause: str, steps: list, validation: Optional[str] = None, risk_level: str = "low") -> str:
        if not self.api_key:
            return json.dumps({"status": "error", "message": "API key required. Set FIXGRAPH_API_KEY or pass api_key."})
        norm = []
        for s in steps:
            d = s.model_dump() if hasattr(s, "model_dump") else dict(s)
            if "code_language" in d: d["codeLanguage"] = d.pop("code_language")
            norm.append({k: v for k, v in d.items() if v is not None})
        payload: dict = {"issue_id": issue_id, "title": title, "root_cause": root_cause, "steps": norm, "risk_level": risk_level}
        if validation: payload["validation"] = validation
        try:
            r = _post("/api/fixes", payload, self.api_key)
            return json.dumps({"status": "created", "id": r["id"], "issue_id": r.get("issue_id", issue_id), "title": r["title"], "trust_score": r.get("trust_score", 0)})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})
