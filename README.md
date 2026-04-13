# Research Agent

A Python research agent that can:
- take a topic,
- search the web for multiple angles,
- fetch and summarize source content,
- produce a structured markdown research report.

The agent works in two modes:
- Default mode: extractive summarization (no API key required).
- LLM-enhanced mode: richer synthesis if `OPENAI_API_KEY` is set.

## Setup

```powershell
cd d:\Dev_Tutorials
python -m pip install -r research_agent\requirements.txt
```

## Run

```powershell
python -m research_agent.cli "Impact of AI on healthcare" --max-sources 8 --output ai_healthcare_report.md
```

## Optional LLM Enhancement

Set environment variables if you want a model-written report:

```powershell
$env:OPENAI_API_KEY="your_key"
$env:OPENAI_MODEL="gpt-4.1-mini"
# Optional for OpenAI-compatible providers
$env:OPENAI_BASE_URL="https://api.openai.com/v1"
```

## Output format

The report includes:
- Executive Summary
- Detailed Findings
- Sources / references

In LLM mode, it generates a full analyst-style research structure.

## Tests

```powershell
python -m pytest research_agent/tests -q
```
