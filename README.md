# Local-First Agent Search

A small, offline-first search service for a person's own local documents and datasets. It provides a local HTTP API, JSON-lines CLI bridge, profile preferences, and an MCP-compatible stdio tool server. It does not crawl private databases or search people by name.

## Features

- Persistent SQLite index and audit log
- UTF-8 text/Markdown/JSON/CSV/HTML/XML ingestion from a configured directory
- Unicode-aware tokenization and BM25-style lexical ranking
- Private collections hidden by default; local grants scope access by collection, source, purpose, and expiry
- Revocable local grants and audit events
- Read-only agent tools that cannot retrieve private documents or access the network
- Profile preferences for locale, languages, default collections, and result format
- Connector capability endpoint describing what is and is not implemented

## Run locally

Requires Python 3.10+.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export SEARCH_API_TOKEN="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

The API binds to localhost. Do not bind it to a public interface or expose it through a tunnel. Admin endpoints are disabled unless `SEARCH_API_TOKEN` is configured. Put files to index under `./data/ingest/`; API paths must be relative to that directory. Only the documented safe text types and configured size limit are supported.

## Search and configuration

`POST /search` searches local indexed documents. `GET /connectors` reports connector status; it does not connect to Google, Bing, Yahoo, DuckDuckGo, Firefox, Tor/onion services, or private providers. Provider integrations require approved interfaces and are deliberately not implemented here.

Profiles are local settings, not accounts. Save one with the admin token:

```bash
curl -X POST http://127.0.0.1:8000/profiles \
  -H "Authorization: Bearer $SEARCH_API_TOKEN" -H "Content-Type: application/json" \
  -d '{"profile_id":"default","display_name":"Local user","locale":"en","languages":["en","es"],"default_collections":["default"],"result_format":"json"}'
```

## Private local collections

Private documents are excluded from normal search and agent tools. A local owner can create a scoped grant via `POST /access-grants`, then use its `grant_id` and the exact stated purpose in `POST /search`. A grant applies to one collection and one source only and can be revoked at `POST /access-grants/revoke`. These controls do not establish another person's identity or substitute for legal consent/provider authorization.

## Offline agents

JSON-lines bridge: `python -m app.agent_server`; MCP-compatible stdio: `python -m app.mcp_server`. Both expose only non-private local content and make no network calls. Configure only in a trusted agent runtime.

## Tests

```bash
python -m unittest discover -s tests
```

## Scope and next steps

This remains a prototype. It does not include external search connectors, webhooks, executable extensions, a web UI, OCR, archive parsing, or multi-user authentication. Webhooks and extensions need additional SSRF, signing, secret-management, and sandbox review before implementation. Read [AUDIT.md](AUDIT.md) before use.
