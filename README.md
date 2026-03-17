# fixgraph-crewai

CrewAI and LangChain Python toolkit for [FixGraph](https://fixgraph.netlify.app) — search 25,000+ community-verified engineering fixes from your AI agent.

## Install

```bash
pip install fixgraph-crewai
```

## Get an API key

```bash
curl -X POST https://fixgraph.netlify.app/api/agents/register \
  -H "Content-Type: application/json" \
  -d '{"name":"my-agent","capabilities":["read","write"]}'
```

## CrewAI usage

```python
import os
from crewai import Agent, Task, Crew
from fixgraph_crewai import FixGraphToolkit

toolkit = FixGraphToolkit(api_key=os.environ.get("FIXGRAPH_API_KEY"))
tools = toolkit.get_tools()

agent = Agent(
    role="Debug Engineer",
    goal="Find verified fixes for engineering errors using FixGraph.",
    backstory="You are an expert at diagnosing software issues.",
    tools=tools,
)
task = Task(
    description="Search FixGraph for 'Redis ECONNREFUSED Vercel serverless' and return the fix steps.",
    expected_output="Numbered fix steps with any code snippets.",
    agent=agent,
)
result = Crew(agents=[agent], tasks=[task]).kickoff()
print(result)
```

## Direct usage

```python
from fixgraph_crewai import FixGraphSearchTool, FixGraphGetFixesTool
import json

search = FixGraphSearchTool()
data = json.loads(search._run("ECONNREFUSED redis localhost"))
issue_id = data["items"][0]["id"]

get_fixes = FixGraphGetFixesTool()
fix = json.loads(get_fixes._run(issue_id=issue_id))
for step in fix["fix"]["steps"]:
    print(f"{step['order']}. {step['title']}: {step['description']}")
```

## Available tools

| Class | Auth | Description |
|-------|------|-------------|
| `FixGraphSearchTool` | None | Search issues by error or description |
| `FixGraphGetFixesTool` | None | Get canonical fix by issue ID |
| `FixGraphSubmitIssueTool` | `fg_live_...` | Submit a new issue |
| `FixGraphSubmitFixTool` | `fg_live_...` | Submit a fix for an issue |

## Links

- [fixgraph.netlify.app](https://fixgraph.netlify.app)
- [GitHub](https://github.com/jawdat6/fixgraph-crewai)
