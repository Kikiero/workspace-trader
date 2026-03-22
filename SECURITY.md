# Security

## API keys & secrets

- **Do not commit** real API keys, tokens, or passwords.
- Copy `trading-orchestrator/ENV.example` to a **local** `.env` or `ENV` file (both are gitignored) and fill values there, or use `export` in your shell only.
- Tracked files use **placeholders only** (empty `KEY=` lines in `ENV.example`).

## If a key was ever committed

1. Rotate the key at the provider (NewsAPI, TuShare, Alpha Vantage, broker API, etc.).
2. Remove it from git history (`git filter-repo` / BFG) or consider the repo compromised for that key.

## Reporting

If you find committed credentials, rotate them immediately and remove from history before pushing public GitHub.
