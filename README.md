# Agentropy — "See it. Improve it."

The simplest agent observability platform: standard OpenTelemetry capture,
a beautiful dashboard, and — the actual product — an AI insight engine that
turns observations into **predictions and concrete improvement proposals**
(cost, latency, failures).

Open-core: the capture SDKs are open source; the insight engine and the
hosted backend are the commercial product. English is the primary language
for the UI, docs, and prompts.

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

- **Capture is 100% standard OpenTelemetry** (GenAI semantic conventions).
  We deliberately do not reinvent instrumentation.
- **Metrics store** is SQLite in this stage so it runs with zero infra
  (TODO: ClickHouse).
- **SaaS data** (users, workspaces, API keys, subscriptions) lives in
  **Supabase Postgres** — never in the metrics DB.
- **Billing** is **Polar** (checkout + webhooks). Tiers: Starter $19/mo,
  Pro $49/mo, unlimited seats on both.

## Repo layout (screaming architecture)

```
apps/
  api/
    app/
      main.py            # wires routers only
      core/              # config (env), metrics sqlite client,
                         # supabase client, shared pricing table
      auth/              # X-API-Key + Supabase JWT dependencies
      ingest/            # router/service/schemas — JSON batch + OTLP receiver
      traces/            # router/service/schemas — span queries
      insights/          # router/service/schemas + graph.py (LangGraph engine)
      billing/           # router/service/schemas — Polar checkout + webhooks
      workspaces/        # router/service/schemas — projects + API keys (Supabase)
    requirements.txt
    data/                # local sqlite DB (gitignored)
  web/
    app/                 # routes only: /, /dashboard, /pricing, /docs, /login
    features/
      landing/           # marketing sections
      dashboard/         # real-data dashboard (client components)
      pricing/           # Polar checkout flow
      docs/              # one-prompt guide + SDK install tabs
      auth/              # Supabase magic-link login
    components/ui/       # shared UI primitives
    lib/                 # api client, pricing, supabase browser client
packages/
  sdk-py/                # pip package `agentropy` — one-line OTel init (Python)
  sdk-ts/                # npm package `@agentropy/sdk` — one-line OTel init (Node)
supabase/
  migrations/001_init.sql  # SaaS schema: profiles, workspaces, api_keys,
                           # subscriptions, usage_events (+ RLS)
docs/
  one-prompt-shot.md     # the English prompt template for coding agents
```

The backend is organized in **domain vertical slices** (ingest, traces,
insights, billing, workspaces, auth) — not technical layers. Each domain
owns its router, service, and schemas. `main.py` only wires routers.

The frontend mirrors this: `app/` holds routes only; each feature lives in
`features/<domain>/`; shared code in `components/ui/` and `lib/`.

## Run it locally

Prerequisites: Node 20+, pnpm, Python 3.10+.

```bash
# 1. Install JS workspaces
pnpm install

# 2. Build everything (Next.js web + TS SDK)
pnpm build

# 3. Web dashboard (dev)
pnpm --filter @agent-observability/web dev   # http://localhost:3000

# 4. API (separate terminal)
cd ~/workspace/agent-observability
./.venv/bin/uvicorn app.main:app --app-dir apps/api --port 8000
# API_KEY=dev-key is the dev default; override via env in real use.
```

Quick roundtrip:

```bash
curl -X POST localhost:8000/v1/ingest \
  -H "X-API-Key: dev-key" -H "Content-Type: application/json" \
  -d '{"spans":[{"trace_id":"abc","span_id":"def","name":"agent.run","attributes":{"gen_ai.system":"openai"},"duration_ms":120,"is_error":false}]}'

curl localhost:8000/v1/traces -H "X-API-Key: dev-key"

# Run the insight engine over recent spans:
curl -X POST localhost:8000/v1/insights/run -H "X-API-Key: dev-key"
curl localhost:8000/v1/insights -H "X-API-Key: dev-key"
```

Python SDK end-to-end (with the API running):

```bash
cd packages/sdk-py
pip install -e .
python - <<'EOF'
import agentropy
from opentelemetry import trace
agentropy.init(api_key="dev-key", service_name="demo")
tracer = trace.get_tracer("demo")
with tracer.start_as_current_span("agent.run") as span:
    for k, v in agentropy.genai_attrs(
        system="openai", request_model="gpt-4o",
        input_tokens=1200, output_tokens=300).items():
        span.set_attribute(k, v)
agentropy.shutdown()
print("span sent — check GET /v1/traces")
EOF
```

TypeScript SDK end-to-end:

```bash
cd packages/sdk-ts   # already built by `pnpm build`
node - <<'EOF'
const { init, shutdown, genaiAttrs, getTracer } = require("./dist/index.js");
init({ apiKey: "dev-key", serviceName: "demo-ts" });
const tracer = getTracer();
tracer.startActiveSpan("agent.run", (span) => {
  span.setAttributes(genaiAttrs({ system: "anthropic", requestModel: "claude-opus-4-6", inputTokens: 800, outputTokens: 150 }));
  span.end();
});
setTimeout(() => shutdown().then(() => console.log("span sent — check GET /v1/traces")), 2000);
EOF
```

## Environment variables

| Variable | Required for | Default |
|---|---|---|
| `API_KEY` | Ingest/query auth (dev) | `dev-key` (never ship this) |
| `DB_PATH` | Metrics sqlite location | `apps/api/data/spans.db` |
| `SUPABASE_URL` | SaaS DB + auth | — (SaaS routes → 503 without it) |
| `SUPABASE_SERVICE_ROLE_KEY` | SaaS DB writes | — |
| `SUPABASE_JWT_SECRET` | Validating Supabase JWTs | — |
| `NEXT_PUBLIC_SUPABASE_URL` | Web login | — (login shows "not configured") |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Web login | — |
| `POLAR_ACCESS_TOKEN` | Billing checkout | — (billing → 503 without it) |
| `POLAR_WEBHOOK_SECRET` | Webhook signature check | — |
| `POLAR_STARTER_PRODUCT_ID` | $19/mo product | — |
| `POLAR_PRO_PRODUCT_ID` | $49/mo product | — |
| `POLAR_SERVER` | Polar API base | `https://api.polar.sh` |
| `POLAR_SUCCESS_URL` | Post-checkout redirect | `http://localhost:3000/dashboard` |
| `OPENROUTER_API_KEY` | Optional LLM polish of insight wording via OpenRouter (rules are the default) | — |
| `OPENROUTER_MODEL` | Mid-tier model for the polish step | `openai/gpt-4o-mini` |
| `NEXT_PUBLIC_AGENTROPY_API_URL` | Web → API base URL | `http://localhost:8000` |
| `NEXT_PUBLIC_AGENTROPY_API_KEY` | Pre-fill dashboard key | — (or enter in the dashboard; stored in localStorage) |

## Supabase setup (manual steps)

1. Create a project at supabase.com.
2. SQL Editor → paste `supabase/migrations/001_init.sql` → Run.
   Creates: `profiles`, `workspaces`, `api_keys`, `subscriptions`,
   `usage_events` (+ RLS policies).
3. Project Settings → API: copy the **Project URL** → `SUPABASE_URL`,
   the **service_role** key → `SUPABASE_SERVICE_ROLE_KEY` (backend only,
   never expose), and the **anon** key → `NEXT_PUBLIC_SUPABASE_ANON_KEY`
   (web).
4. Project Settings → API → **JWT Secret** → `SUPABASE_JWT_SECRET`
   (backend validates `Authorization: Bearer` JWTs with it, HS256).
5. Enable Email auth (magic link) for `/login`.
6. Without these vars, SaaS routes (`/v1/workspaces/*`, user-gated
   `/v1/billing/checkout`) answer **503** with a clear message — never fake.

## Polar setup (manual steps)

1. Create an organization at polar.sh.
2. Products → create **"Agentropy Starter"** ($19/mo recurring) and
   **"Agentropy Pro"** ($49/mo recurring) as subscription products.
3. Copy each product's ID → `POLAR_STARTER_PRODUCT_ID` /
   `POLAR_PRO_PRODUCT_ID`.
4. Settings → Developers → create an access token → `POLAR_ACCESS_TOKEN`.
5. Settings → Webhooks → add endpoint
   `https://<your-api>/v1/billing/webhook` → copy the signing secret →
   `POLAR_WEBHOOK_SECRET`.
6. Without these vars, billing routes answer **503** with setup instructions.

## The insight engine (LangGraph)

`apps/api/app/insights/graph.py` is a `StateGraph` with six nodes:

1. **load_traces** — pulls recent spans from the metrics store.
2. **compute_stats** — tokens/cost per agent+model, latency p50/p95,
   error rate, tool failure counts, per-day buckets.
3. **forecast** — least-squares linear projection of daily cost and p95
   latency for the next 7/30 days (honest about thin history).
4. **detect_issues** — rules comparing a recent window vs baseline:
   error-rate spike, p95 latency regression, cost-per-run growth,
   repeated identical tool failures, input-token bloat.
5. **propose** — turns issues + forecasts into insights
   (`prediction` | `warning` | `proposal`) with concrete suggested actions.
   If `OPENROUTER_API_KEY` is set, an LLM (via OpenRouter) may polish the wording — facts always
   come from the rules; failures fall back silently to rule text.
6. **persist** — saves insights to the `insights` table.

Trigger: `POST /v1/insights/run` (X-API-Key). Read: `GET /v1/insights`.
TODO: run on a schedule (cron/worker), per-workspace scoping.

## What's real vs stubbed (honest TODOs)

| Area | Current state | TODO |
|---|---|---|
| Trace storage | SQLite (`apps/api/data/spans.db`) | Replace with ClickHouse |
| Ingest auth | `X-API-Key` env default + hashed per-workspace keys in Supabase (when configured) | Key scopes, rotation |
| SaaS auth | Supabase JWT (magic link) | — (real when Supabase configured) |
| Billing | Polar checkout + webhooks (real when configured) | Trials via Polar, plan limits enforcement |
| Insight engine | Real LangGraph pipeline: stats, forecasts, rule detections, proposals | Scheduled runs, per-workspace scoping, LLM judges |
| Tenancy | Single-tenant spans; workspaces exist in Supabase | Scope spans/insights per workspace |
| SDK distribution | Local only | Publish `agentropy` to PyPI, `@agentropy/sdk` to npm |
| License | Undecided — no LICENSE file yet | Choose (MIT intended for SDKs) |

## Roadmap

1. ClickHouse storage, retention policies, per-workspace scoping.
2. Scheduled insight runs + weekly digest.
3. Publish SDKs; agent-optimized docs site (llms.txt-style).
4. Tighter improvement loop: propose → verify → apply.
