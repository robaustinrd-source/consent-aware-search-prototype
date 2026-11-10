# Consent-Aware Local Search Prototype

A local-first, consent-aware search and indexing system designed for offline AI agents and human users.

This prototype is intentionally narrow and safe:
- local collections are searchable without cloud access
- public sources can be queried only when configured
- private or sensitive sources require consent
- source access is auditable and revocable
- agent interfaces use a small, explicit tool surface

## What is included

- FastAPI backend for search and consent APIs
- local document indexing for text-based files
- in-memory consent workflow
- simple offline agent bridge withstdio-friendly tool calls
- sample collection for testing
- minimal file layout ready for extension

## Safety posture

This project does not build a universal private data search engine. Instead, it creates a safe pattern:
- the user owns the data or has permission
- a source is explicitly allowed
- consent is captured before sensitive access
- audit events are generated for each request

## Quickstart

1. Create a virtual environment
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

2. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

3. Run the API server
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

4. Explore the API
   ```bash
   http://localhost:8000/docs
   ```

5. Run the CLI demo
   ```bash
   python -m app.agent_server --demo
   ```

## Example requests

### Search local content

```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "consent workflow",
    "collections": ["default"],
    "include_private": false
  }'
```

### Create a consent request

```bash
curl -X POST http://localhost:8000/consent/request \
  -H "Content-Type: application/json" \
  -d '{
    "subject_id": "person-001",
    "source_id": "source-1",
    "purpose": "background review",
    "requested_by": "agent-01"
  }'
```

### Approve a consent request

```bash
curl -X POST http://localhost:8000/consent/approve \
  -H "Content-Type: application/json" \
  -d '{
    "request_id": "request-uuid",
    "approved_by": "human-owner"
  }'
```

## Folder layout

```text
app/
  __init__.py
  agent_server.py
  consent.py
  indexer.py
  main.py
  models.py
  search_engine.py
sampledocs/
  knowledge.md
  profile.txt
```

## Future extensions

- source adapters for Bing, DuckDuckGo, Yahoo, private datasets
- webhook emitters for search completion or consent activity
- extension security sandbox
- local language model integration
- stronger persistence and multi-user auth
- MCP protocol adapters for wider AI agent compatibility

## License

MIT
