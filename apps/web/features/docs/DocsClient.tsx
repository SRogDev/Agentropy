"use client";

import { useState } from "react";
import Link from "next/link";

function Code({ children }: { children: string }) {
  return (
    <pre className="overflow-x-auto rounded-xl bg-zinc-900 p-4 font-mono text-xs leading-relaxed text-zinc-100">
      {children}
    </pre>
  );
}

const PY_INSTALL = `pip install agentropy`;
const NPM_INSTALL = `npm install @agentropy/sdk`;

const PY_SNIPPET = `import agentropy

agentropy.init(
    api_key="YOUR_API_KEY",          # from your workspace
    endpoint="https://api.agentropy.dev",
)

# tag spans with GenAI conventions
from opentelemetry import trace
tracer = trace.get_tracer("my-agent")
with tracer.start_as_current_span("agent.run") as span:
    for k, v in agentropy.genai_attrs(
        system="openai", request_model="gpt-4o-mini",
        input_tokens=1200, output_tokens=300,
    ).items():
        span.set_attribute(k, v)`;

const TS_SNIPPET = `import { init, genaiAttrs, getTracer } from "@agentropy/sdk";

init({ apiKey: "YOUR_API_KEY", endpoint: "https://api.agentropy.dev" });

const tracer = getTracer();
tracer.startActiveSpan("agent.run", (span) => {
  span.setAttributes(genaiAttrs({
    system: "openai", requestModel: "gpt-4o-mini",
    inputTokens: 1200, outputTokens: 300,
  }));
  // ... your agent logic ...
  span.end();
});`;

const PROMPT_TEMPLATE = `I want observability for my AI agents using Agentropy.

Setup: pip install agentropy, then agentropy.init(api_key="YOUR_API_KEY").

Instrument my codebase so Agentropy captures ALL of the following:
1. Token usage and estimated cost — per LLM call, per agent run, per session.
2. Latency — per LLM call, per tool call, end-to-end per run.
3. Agent context — inputs, retrieved documents, conversation state (no PII).
4. Tool calls — name, arguments (redacted where sensitive), duration, outcome.
5. Errors — exceptions, retries, fallbacks with full stack context.
6. Trajectories — the complete step-by-step path of every run, one trace.

Rules: use the SDK's one-line init(); tag spans with GenAI semantic
conventions (gen_ai.*); correlate everything under one trace per run;
never send secrets or raw PII; keep instrumentation in one reviewable module.

After instrumenting, verify: run one agent task end-to-end and confirm the
trace appears in the Agentropy dashboard with tokens, cost, latency,
tool calls, and the full trajectory visible.`;

export default function DocsClient() {
  const [tab, setTab] = useState<"py" | "ts">("py");

  return (
    <main className="mx-auto max-w-4xl px-6 py-16">
      <header className="flex items-center justify-between">
        <Link href="/" className="text-lg font-semibold tracking-tight">
          Agentropy
        </Link>
        <Link
          href="/dashboard"
          className="rounded-full bg-zinc-900 px-5 py-2 text-sm font-medium text-white hover:bg-zinc-700"
        >
          Open dashboard
        </Link>
      </header>

      <h1 className="mt-12 text-4xl font-semibold tracking-tight">Docs</h1>
      <p className="mt-3 text-lg text-zinc-600">
        Written for coding agents first, humans second. The fastest path is
        the one-prompt setup.
      </p>

      <section className="mt-12">
        <h2 className="text-2xl font-semibold tracking-tight">
          One-prompt setup
        </h2>
        <p className="mt-3 text-zinc-600">
          Describe what you want to observe in a single prompt. Paste it into
          your coding agent — it generates the complete instrumentation.
        </p>
        <div className="mt-4">
          <Code>{PROMPT_TEMPLATE}</Code>
        </div>
      </section>

      <section className="mt-12">
        <h2 className="text-2xl font-semibold tracking-tight">Install the SDK</h2>
        <div className="mt-4 flex gap-2">
          {(["py", "ts"] as const).map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`rounded-full px-5 py-2 text-sm font-medium ${
                tab === t
                  ? "bg-zinc-900 text-white"
                  : "border border-zinc-300 text-zinc-600 hover:border-zinc-500"
              }`}
            >
              {t === "py" ? "Python" : "TypeScript"}
            </button>
          ))}
        </div>
        <div className="mt-4 space-y-4">
          <Code>{tab === "py" ? PY_INSTALL : NPM_INSTALL}</Code>
          <Code>{tab === "py" ? PY_SNIPPET : TS_SNIPPET}</Code>
        </div>
      </section>

      <section className="mt-12">
        <h2 className="text-2xl font-semibold tracking-tight">What gets captured</h2>
        <ul className="mt-4 grid gap-3 text-sm text-zinc-600 md:grid-cols-2">
          {[
            "Token usage + estimated cost per call, run, session",
            "Latency per LLM call, tool call, and end-to-end run",
            "Agent context: inputs, retrieved docs, conversation state",
            "Tool calls: name, args (redacted), duration, outcome",
            "Errors: exceptions, retries, fallbacks",
            "Full trajectories as a single trace",
          ].map((f) => (
            <li key={f} className="rounded-xl border border-zinc-200 bg-white p-4">
              {f}
            </li>
          ))}
        </ul>
      </section>

      <section className="mt-12 rounded-2xl bg-zinc-900 p-8 text-white">
        <h2 className="text-xl font-semibold">Then the insight engine takes over</h2>
        <p className="mt-2 text-sm leading-relaxed text-zinc-300">
          Once spans flow, run the analysis (dashboard → “Run analysis”, or{" "}
          <span className="font-mono">POST /v1/insights/run</span>). Agentropy
          computes real statistics, forecasts cost and latency, detects
          anomalies, and proposes concrete fixes.
        </p>
      </section>
    </main>
  );
}
