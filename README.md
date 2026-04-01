# Hence

> ARK: Survival Ascended player tracking — Discord bot + web dashboard

Hence monitors ARK servers (official via BattleMetrics, private via RCON), logs player activity tied to their persistent EOS (Epic Online Services) IDs, de-anonymizes players using generic names like "123", and exposes everything through Discord slash commands and a web dashboard.

## Quick start

```bash
cp .env.example .env
# Fill in DISCORD_TOKEN, DISCORD_GUILD_ID, BATTLEMETRICS_API_KEY, etc.

docker compose up --build
```

Run database migrations (first time, or after schema changes):

```bash
docker compose run --rm api alembic upgrade head
```

## Architecture

```
[BattleMetrics API] ──┐
[RCON (private svr)] ──┼──► [FastAPI :8000] ──► [PostgreSQL :5432]
                        │           │
                        │    ┌──────┴──────┐
                        │    ▼             ▼
                        │  [Discord Bot] [React Dashboard :3000]
```

- **FastAPI** is the central hub — polls BattleMetrics in the background, exposes REST endpoints
- **Discord bot** calls FastAPI over HTTP — never touches the DB directly
- **EOS ID** is the single source of truth for player identity

## Services

| Service | Port | Description |
|---|---|---|
| `api` | 8000 | FastAPI backend + BattleMetrics poller |
| `db` | 5432 | PostgreSQL |
| `bot` | — | Discord bot |
| `dashboard` | 3000 | React frontend (Phase 4) |

## Discord commands (Phase 1)

| Command | Description |
|---|---|
| `/whois <eos_id>` | Look up a player — all names, first/last seen, session count |
| `/online` | List all currently online players across tracked servers |
| `/search <name>` | Search by partial player name |

## Development

Install API dependencies locally:

```bash
cd api && pip install -r requirements.txt
```

Run tests:

```bash
pytest
```

Run linter:

```bash
ruff check .
```

## Adding a server to track

Use the API directly or the Discord bot (admin commands added in Phase 3):

```bash
curl -X POST http://localhost:8000/servers/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Official NA-PVP-123", "type": "official", "battlemetrics_id": "12345678"}'
```

## Build phases

- **Phase 1** ✅ — Bot + BattleMetrics polling, `/online`, `/whois`, `/search`
- **Phase 2** — Alias history, `/aliases`, `/history`, name change detection
- **Phase 3** — RCON integration, `/addserver`, `/removeserver`
- **Phase 4** — React dashboard
- **Phase 5** — CI/CD, branch protection, deploy pipeline

## Environment variables

See [.env.example](.env.example) for all required variables.
