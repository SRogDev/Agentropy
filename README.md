# Agentropy — "See it. Improve it."

The simplest agent observability platform: **standard OpenTelemetry capture**, a beautiful dashboard, and — the actual product — an **AI insight engine** that turns observations into predictions and concrete improvement proposals (cost, latency, failures).

Open-core: the capture SDKs are open source; the insight engine and the hosted backend are the commercial product. English-first UI, docs, and prompts.

## Architecture

```
┌──────────────┐      OTLP/HTTP       ┌──────────────────┐
│  your agent  │ ───────────────────▶ │   apps/api       │
│  + SDK       │   (standard OTel)    │   FastAPI          │
└──────────────┘                      │  ingest → store  │
                                      │  LangGraph       │
                                      │  insight engine  │
                                      └────────┬─────────┘
                                               │  GET /v1/traces
                                               │  GET /v1/insights
                                      ┌────────▼─────────┐
                                      │   apps/web       │
                                      │   Next.js        │
                                      │   real-data      │
                                      │   dashboard      │
                                      └──────────────────┘
```

- **Capture is 100% standard OpenTelemetry** (GenAI semantic conventions) — no reinvented instrumentation.
- **Metrics store** is SQLite at this stage (zero infra; ClickHouse later).
- **SaaS data** (users, workspaces, API keys, subscriptions) lives in **Supabase Postgres** — never in the metrics DB.
- **Billing** is **Polar** (checkout + webhooks). Tiers: Starter $19/mo, Pro $49/mo, unlimited seats on both.
- The **insight engine** is a LangGraph StateGraph: load traces → compute stats → forecast (7/30d) → detect issues (rules vs baseline) → propose (`prediction` | `warning` | `proposal`) → persist. Optional LLM polish via OpenRouter — facts always come from the rules.

## Status

- **v2 done (2026-09-26):** LangGraph insight engine (verified predictions/warnings/proposals), real-data dashboard, marketing landing + `/pricing` `/docs` `/login`, Polar billing, Supabase DB + auth; insight LLM polish via OpenRouter (`openai/gpt-4o-mini`).
- **PAUSED — awaiting setup:** Supabase project + migration + keys; Polar org/products/token/webhook; OpenRouter key.
- **Next:** apply migration, wire billing, live-test the insight loop.

## Run it locally

Prerequisites: Node 20+, pnpm, Python 3.10+.

```bash
pnpm install && pnpm build
pnpm --filter @agent-observability/web dev   # http://localhost:3000

# API (separate terminal)
./.venv/bin/uvicorn app.main:app --app-dir apps/api --port 8000
# API_KEY=dev-key is the dev default; override via env in real use.
```

Quick roundtrip: `POST /v1/ingest` spans → `GET /v1/traces` → `POST /v1/insights/run` → `GET /v1/insights`. Env vars, Supabase/Polar setup, and SDK examples are documented in the repo.

## Structure

```
apps/
├── api/      # FastAPI: ingest, traces, insights (LangGraph), billing, workspaces, auth
└── web/      # Next.js: routes + features/<domain>/ (screaming architecture)
packages/
├── sdk-py/   # `agentropy` — one-line OTel init (Python)
└── sdk-ts/   # `@agentropy/sdk` — one-line OTel init (Node)
supabase/     # migrations/001_init.sql — SaaS schema + RLS
docs/         # one-prompt-shot.md — prompt template for coding agents
```

The backend is organized in domain vertical slices (ingest, traces, insights, billing, workspaces, auth) — each domain owns its router, service, and schemas.

## License

No license file yet (open-core intended: MIT for the SDKs).
