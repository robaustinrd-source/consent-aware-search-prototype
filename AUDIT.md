# Audit notes and integration boundaries

## Fixes in this increment

- Fixed a private-data authorization bug: a grant now permits only its exact collection **and source**, not every private source sharing that collection.
- Added regression coverage for cross-source isolation and persisted locale/language profile settings.
- Added profile preferences for interface locale, language preferences, default collections, and output format.
- Added a connector capability/status endpoint. It is descriptive only; no external provider is queried.

## Current limitations

- Google, Bing, Yahoo, DuckDuckGo, Firefox, and private-data integrations are not implemented. Add each only through provider-supported APIs, browser extension interfaces, or owner-authorized imports.
- Onion routing/crawling is disabled and not implemented. This prototype does not crawl Tor or bypass access controls.
- Webhook delivery and executable extensions are not implemented. Do not load arbitrary extension code or send callbacks to user-provided URLs until a sandbox, endpoint validation, signing, retries, and secret management are designed and tested.
- File ingestion supports only UTF-8 text-based TXT, Markdown, JSON, CSV, HTML, and XML under a size limit. It does not support “all formats”; archives and active content are intentionally excluded.
- Profiles and local grants are single-owner local controls, not multi-user identity proof or legally sufficient consent. Keep the service bound to localhost and do not use for consequential decisions.

## Important security caveat

The bearer token is a single local admin secret. It is not a production authentication system; anyone who can read the process environment or access the local machine may be able to use it. Use a trusted device and filesystem, keep backups protected, and do not expose the API to a public network.
