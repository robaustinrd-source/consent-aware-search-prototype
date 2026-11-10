# Local-first search prototype

This project is a local-first, consent-aware search prototype for offline AI agents and trusted local users. It is intentionally narrow and bounded by design.

## What was added in this increment

- local connector registry and provider capability scaffolding
- webhook event manager for async notifications
- extension registry and sandbox layer stubs
- local auth/session helper scaffold
- OCR processing scaffold for image/PDF workflows
- multilingual detection and normalization helpers
- README documentation for architecture and safety boundaries

## Current support level

- local document indexing
- local storage and audit log
- consent-scoped private access
- agent/CLI interfaces
- terminal-only hosting on localhost
- provider capability discovery, not live network integration
- extension and webhook infrastructure scaffolding, not public execution

## Important boundaries

These features are purposely not a universal search engine over all sectors and pipelines.

- Google, Bing, Yahoo, DuckDuckGo, Firefox, Tor/onion, and private-provider integrations are not live. They are represented as allowlisted provider scaffolds only.
- Webhooks do not send to arbitrary endpoints until destination validation, signing, retries, and secret rotation are designed.
- Extensions are not executed in production; they are sandbox stubs only.
- OCR and multilingual pipelines are placeholders. Real implementations require vendor-specific tooling and user-approved workflows.
- This does not search people or institutions without explicit authorization and legal/provider support.

## Next recommended implementation path

1. Real auth provider integration (OIDC or equivalent)
2. UI and settings page
3. connector adapters behind allowlists and API-key checks
4. sandboxed extension runtime
5. OCR pipeline + multilingual indexing
6. production webhooks and job queue
7. full audit, retention, and deletion workflows

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export SEARCH_API_TOKEN="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
python -m app.cli serve --host 127.0.0.1 --port 8000
```

Then use the CLI or API as documented in the project docs.
