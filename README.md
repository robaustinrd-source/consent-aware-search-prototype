# Local-First Agent Search

A small, offline-first search service for a person's own local documents and datasets. It provides a local HTTP API, JSON-lines CLI bridge, profile preferences, and an MCP-compatible stdio tool server. It does not crawl private databases or search people by name.

## Terminal setup

Requires Python 3.10+.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m app.cli serve
```

The server listens only on `127.0.0.1`. On first launch it generates and prints a local admin token; save it in your shell environment before using indexing or settings commands:

```bash
export SEARCH_API_TOKEN='paste-the-generated-token-here'
```

The token is not persisted by the application. To choose your own, set `SEARCH_API_TOKEN` before starting the server. Do not bind to a public interface or expose it through a tunnel. Admin endpoints are disabled if no token is configured when the app starts.

## Terminal commands

```bash
python -m app.cli search "consent workflow"
python -m app.cli collections
python -m app.cli interactive
```

Put supported files under `./data/ingest/` (or set `SEARCH_INGEST_DIR`). Index one file or asynchronously sync the directory:

```bash
python -m app.cli index ./data/ingest/notes.md --collection default
python -m app.cli sync --collection default --concurrency 4
```

`sync` uses async HTTP requests with bounded concurrency and retries transient failures. It does not execute shell commands or arbitrary file contents. Concurrency is capped at eight. The CLI only connects to a loopback API URL and the server refuses non-loopback bind addresses.

## API and data

SQLite persists the local index and audit log. Ingest is limited to UTF-8 TXT, Markdown, JSON, CSV, HTML, and XML under the configured size limit. API paths must remain inside the ingest directory. `POST /search` searches local indexed documents. `GET /connectors` reports provider status; Google, Bing, Yahoo, DuckDuckGo, Firefox, onion services, and private providers are not connected in this prototype.

## Private local collections

Private documents are excluded from normal search and agent tools. A local owner can create a scoped grant via `POST /access-grants`, then use its `grant_id` and exact purpose in `POST /search`. A grant applies to one collection and one source and can be revoked. These controls do not establish another person's identity or substitute for legal consent/provider authorization.

## Offline agents

JSON-lines bridge: `python -m app.agent_server`; MCP-compatible stdio: `python -m app.mcp_server`. Both expose only non-private local content and make no network calls. Configure only in a trusted agent runtime.

## Tests

```bash
python -m unittest discover -s tests
```

## Limitations

This remains a prototype, not a production hosting setup. It has no TLS, multi-user authentication, external search connectors, webhooks, executable extensions, web UI, OCR, archive parsing, or production consent verification. Keep it on a trusted local machine. Review [AUDIT.md](AUDIT.md) before indexing sensitive files.
