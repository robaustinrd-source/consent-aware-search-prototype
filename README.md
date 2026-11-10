# Local-First Agent Search

A small, offline-first search service for a person's own local documents and datasets. It provides a local HTTP API, a JSON-lines CLI bridge, and an MCP-compatible stdio tool server. It does not crawl private databases or search people by name.

## Current prototype features

- Persistent SQLite index and audit log
- Text/Markdown/JSON/CSV/HTML/XML ingestion from a configured directory
- Unicode-aware tokenization and BM25-style lexical ranking
- Private collections hidden by default; optional local-owner grants are scoped by collection, purpose, and expiry
- Revocable local grants and audit events
- Read-only agent tools that cannot retrieve private documents or access the network
- API admin endpoints protected by a bearer token

## Run locally

Requires Python 3.10+.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export SEARCH_API_TOKEN="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

The API binds to localhost. Do not bind it to a public interface or expose it through a tunnel. Admin endpoints are disabled unless `SEARCH_API_TOKEN` is configured. Put files to index under `./data/ingest/`; API paths must be relative to that directory. The ingest service rejects unsupported types, paths outside the root, and files over the configured size.

```bash
cp sampledocs/knowledge.md data/ingest/
curl -X POST http://127.0.0.1:8000/index \
  -H "Authorization: Bearer $SEARCH_API_TOKEN" -H "Content-Type: application/json" \
  -d '{"path":"knowledge.md","collection_id":"default","source_id":"local-files"}'
curl -X POST http://127.0.0.1:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query":"consent workflow","collections":["default"]}'
```

## Private local collections

Mark documents private when indexing. They are excluded from normal search and agent tools. A local owner can create a purpose-limited grant using the admin token:

```bash
curl -X POST http://127.0.0.1:8000/access-grants \
  -H "Authorization: Bearer $SEARCH_API_TOKEN" -H "Content-Type: application/json" \
  -d '{"source_id":"local-files","collection_id":"private","purpose":"review my own files","expires_in_hours":2}'
```

Use the returned `authorization.grant_id` and the exact purpose to search that collection:

```bash
curl -X POST http://127.0.0.1:8000/search \
  -H "Authorization: Bearer $SEARCH_API_TOKEN" -H "Content-Type: application/json" \
  -d '{"query":"account","collections":["private"],"authorization_id":"grant-id","purpose":"review my own files"}'
```

Revoke via `POST /access-grants/revoke` with `{"authorization_id":"grant-id"}`. These local grants are an application access-control feature only: they do not prove a person's identity, establish legal consent, or authorize access to third-party providers. Do not use this prototype for employment, credit, health, government, or other consequential checks.

## Offline agents

JSON-lines CLI:

```bash
python -m app.agent_server --demo
python -m app.agent_server
```

The line-oriented bridge accepts `{"action":"list_collections"}`, `{"action":"search_local","query":"..."}`, and `{"action":"get_document","document_id":"..."}`. It exposes non-private local data only.

MCP-compatible stdio server:

```bash
python -m app.mcp_server
```

It implements initialize, tools/list, and tools/call for `list_collections`, `search_local`, and `get_document`. It uses the same local SQLite index and never makes network calls. Configure it only in an agent you trust; local agent processes can read non-private indexed content.

## Tests

```bash
python -m unittest discover -s tests
```

## Deliberate boundaries and next steps

This is a prototype, not a production security or legal-consent system. It currently has no external search connectors, cloud sync, webhook delivery, extension execution, authentication for multiple users, OCR, or support for arbitrary file formats. Integrate external providers only through their approved APIs and terms; keep connectors opt-in, separately permissioned, and auditable. Any future extension runtime should be sandboxed rather than importing arbitrary plugins into the API process.
