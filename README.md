# Agentropy (working title)

The simplest agent observability platform: standard OpenTelemetry capture,
a beautiful dashboard, and — the actual product — an AI engine that turns
observations into **insights and predictions** (cost, latency, failures, and
concrete improvement proposals).

Open-core: the capture SDKs are open source; the insight engine and the
hosted backend are the commercial product.

## Architecture

```
┌──────────────┐      OTLP/HTTP       ┌──────────────────┐
│  your agent  │ ───────────────────▶ │   apps/api       │
│  + SDK       │   (standard OTel)    │   FastAPI        │
└──────────────┘                      │  ingest → store  │
                                      └────────┬─────────┘
                                               │  GET /v1/traces
                                      ┌────────▼─────────┐
                                      │   apps/web       │
                                      │   Next.js        │
                                      │   dashboard      │
                                      └──────────────────┘
```

- **Capture is 100% standard OpenTelemetry** (GenAI semantic conventions).
  We deliberately do not reinvent instrumentation.
- **Storage** is SQLite in this skeleton so it runs with zero infra.
- **The insight/prediction engine is not built yet** — the dashboard has an
  honest placeholder where it will live.

## Repo layout

```
apps/
  web/            Next.js (App Router, TS, Tailwind) — landing + /dashboard
  api/            FastAPI — ingest, trace query, auth stub
packages/
  sdk-py/         pip package `agentropy` — one-line OTel init (Python)
  sdk-ts/         npm package `@agentropy/sdk` — one-line OTel init (Node)
```

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
cd apps/api
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
API_KEY=dev-key uvicorn app.main:app --reload --port 8000
```

Quick roundtrip:

```bash
curl -X POST localhost:8000/v1/ingest \
  -H "X-API-Key: dev-key" -H "Content-Type: application/json" \
  -d '{"spans":[{"trace_id":"abc","span_id":"def","name":"agent.run","attributes":{"gen_ai.system":"openai"}}]}'

curl localhost:8000/v1/traces -H "X-API-Key: dev-key"
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

## What is stubbed (honest TODOs)

| Area | Current state | TODO |
|---|---|---|
| Trace storage | SQLite (`apps/api/data/spans.db`) | Replace with ClickHouse |
| Auth | `X-API-Key` compared to `API_KEY` env (default `dev-key`) | Hashed per-project keys, scopes, rotation, revocation in Postgres |
| Billing | None | Stripe subscriptions |
| Insight engine | Placeholder panel in the dashboard | The core product: predictions + improvement proposals |
| Tenancy | Single-tenant | Multi-tenant projects, unlimited seats |
| SDK distribution | Local only | Publish `agentropy` to PyPI, `@agentropy/sdk` to npm |
| License | Undecided — no LICENSE file yet | Choose (MIT intended for SDKs) |

## Roadmap

1. Real auth + multi-tenancy + Stripe billing (no free plan at launch; 14-day trial).
2. ClickHouse storage, retention policies.
3. **Insight engine v1**: cost/latency/failure predictions + improvement proposals from observed data.
4. One-prompt-shot setup: describe what to observe, your coding agent generates the instrumentation.
5. Agent-optimized docs (llms.txt-style) so coding agents integrate us in one shot.
