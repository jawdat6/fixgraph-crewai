# fixgraph-crewai

CrewAI tool for [FixGraph](https://fixgraph.netlify.app) — search 25,000+ community-verified engineering fixes directly from your AI crew.

## Install

```bash
pip install fixgraph-crewai
```

## Usage

```python
from crewai import Agent, Task, Crew
from fixgraph_crewai import FixGraphTool

fix_tool = FixGraphTool()

engineer = Agent(
    role="Senior Software Engineer",
    goal="Debug and fix software issues",
    backstory="Expert at diagnosing and resolving complex technical problems",
    tools=[fix_tool],
)

task = Task(
    description="Search for fixes for: TypeError: 'NoneType' object is not subscriptable",
    agent=engineer,
)

crew = Crew(agents=[engineer], tasks=[task])
result = crew.kickoff()
print(result)
```

## Options

| Option | Default | Description |
|--------|---------|-------------|
| `api_key` | `FIXGRAPH_API_KEY` env | Optional API key |
| `base_url` | `https://fixgraph.netlify.app` | FixGraph instance URL |
| `limit` | `3` | Number of results |

## Links

- [fixgraph.netlify.app](https://fixgraph.netlify.app)
- [GitHub](https://github.com/jawdat6/fixgraph-crewai)
