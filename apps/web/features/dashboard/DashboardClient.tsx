"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { Card } from "@/components/ui/ui";
import { apiBase, fetchInsights, fetchTraces, runInsights } from "@/lib/api";
import type { Insight, Span } from "@/lib/api";
import {
  computeStats,
  formatTokens,
  formatUsd,
  summarizeRuns,
} from "./stats";

const KEY_LS = "agentropy_api_key";

function severityColor(s: Insight["severity"]) {
  switch (s) {
    case "high":
      return "bg-red-100 text-red-800";
    case "medium":
      return "bg-amber-100 text-amber-800";
    case "low":
      return "bg-blue-100 text-blue-800";
    default:
      return "bg-zinc-100 text-zinc-600";
  }
}

function typeLabel(t: Insight["type"]) {
  return t === "prediction" ? "Prediction" : t === "warning" ? "Warning" : "Proposal";
}

export default function DashboardClient() {
  const [apiKey, setApiKey] = useState("");
  const [keyInput, setKeyInput] = useState("");
  const [spans, setSpans] = useState<Span[] | null>(null);
  const [insights, setInsights] = useState<Insight[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const stored =
      localStorage.getItem(KEY_LS) || process.env.NEXT_PUBLIC_AGENTROPY_API_KEY || "";
    if (stored) {
      setApiKey(stored);
      setKeyInput(stored);
    }
  }, []);

  const load = useCallback(
    async (key: string) => {
      setLoading(true);
      setError("");
      try {
        const [t, i] = await Promise.all([
          fetchTraces(key, 500),
          fetchInsights(key, 20).catch(() => ({ insights: [] as Insight[] })),
        ]);
        setSpans(t.spans);
        setInsights(i.insights);
      } catch (e) {
        setError(
          e instanceof Error
            ? e.message
            : "Could not reach the API. Is it running?"
        );
        setSpans(null);
        setInsights(null);
      } finally {
        setLoading(false);
      }
    },
    []
  );

  useEffect(() => {
    if (apiKey) load(apiKey);
  }, [apiKey, load]);

  const saveKey = () => {
    const k = keyInput.trim();
    if (!k) return;
    localStorage.setItem(KEY_LS, k);
    setApiKey(k);
  };

  const handleRunInsights = async () => {
    setRunning(true);
    try {
      await runInsights(apiKey);
      const i = await fetchInsights(apiKey, 20);
      setInsights(i.insights);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Insight run failed");
    } finally {
      setRunning(false);
    }
  };

  const runs = spans ? summarizeRuns(spans) : [];
  const stats = spans ? computeStats(runs, spans) : null;

  return (
    <main className="mx-auto max-w-6xl px-6 py-10">
      <header className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <Link href="/" className="text-lg font-semibold tracking-tight">
            Agentropy
          </Link>
          <p className="mt-1 text-sm text-zinc-500">
            What your agents did — and what to do about it.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <input
            type="password"
            value={keyInput}
            onChange={(e) => setKeyInput(e.target.value)}
            placeholder="API key (X-API-Key)"
            className="w-56 rounded-full border border-zinc-300 bg-white px-4 py-2 text-sm outline-none focus:border-zinc-500"
          />
          <button
            onClick={saveKey}
            className="rounded-full bg-zinc-900 px-5 py-2 text-sm font-medium text-white hover:bg-zinc-700"
          >
            Connect
          </button>
        </div>
      </header>

      {!apiKey && (
        <div className="mt-12 rounded-2xl border border-zinc-200 bg-white p-10 text-center">
          <h2 className="text-xl font-semibold">Connect your API key</h2>
          <p className="mx-auto mt-3 max-w-md text-sm text-zinc-600">
            Enter the <span className="font-mono">X-API-Key</span> your agents
            use to send spans (it&apos;s stored only in this browser). The
            dashboard reads live data from{" "}
            <span className="font-mono">{apiBase()}</span>.
          </p>
        </div>
      )}

      {error && (
        <div className="mt-8 rounded-2xl border border-red-200 bg-red-50 p-6 text-sm text-red-800">
          <p className="font-medium">Couldn&apos;t load data</p>
          <p className="mt-1">{error}</p>
          <p className="mt-2 text-red-700">
            Check that the API is running and the key is correct. No sample
            data is shown — what you see here is always real.
          </p>
        </div>
      )}

      {loading && (
        <p className="mt-12 text-center text-sm text-zinc-500">
          Loading live data…
        </p>
      )}

      {apiKey && !loading && !error && spans && (
        <>
          {spans.length === 0 ? (
            <div className="mt-12 rounded-2xl border border-zinc-200 bg-white p-10 text-center">
              <h2 className="text-xl font-semibold">No spans yet</h2>
              <p className="mx-auto mt-3 max-w-md text-sm text-zinc-600">
                Your API is reachable but hasn&apos;t received any spans.
                Instrument an agent with the SDK:
              </p>
              <pre className="mx-auto mt-4 max-w-md overflow-x-auto rounded-xl bg-zinc-900 p-4 text-left font-mono text-xs text-zinc-100">
{`pip install agentropy
import agentropy
agentropy.init(api_key="YOUR_KEY")`}
              </pre>
              <Link
                href="/docs"
                className="mt-4 inline-block text-sm font-medium text-zinc-900 underline"
              >
                Read the one-prompt setup guide
              </Link>
            </div>
          ) : (
            stats && (
              <>
                <div className="mt-8 grid gap-6 md:grid-cols-2">
                  <Card title="Token usage & cost" hint={`${stats.runs} runs`}>
                    <div className="flex items-end gap-8">
                      <div>
                        <p className="text-3xl font-semibold">
                          {formatTokens(stats.totalInput + stats.totalOutput)}
                        </p>
                        <p className="text-sm text-zinc-500">total tokens</p>
                      </div>
                      <div>
                        <p className="text-3xl font-semibold">
                          {formatUsd(stats.totalCost)}
                        </p>
                        <p className="text-sm text-zinc-500">estimated cost</p>
                      </div>
                    </div>
                    <p className="mt-4 text-sm text-zinc-500">
                      {formatTokens(stats.totalInput)} in ·{" "}
                      {formatTokens(stats.totalOutput)} out ·{" "}
                      {(stats.errorRate * 100).toFixed(1)}% error rate
                    </p>
                  </Card>

                  <Card title="Latency" hint="per run">
                    <div className="flex items-end gap-8">
                      <div>
                        <p className="text-3xl font-semibold">
                          {stats.p50Ms != null
                            ? `${(stats.p50Ms / 1000).toFixed(1)}s`
                            : "—"}
                        </p>
                        <p className="text-sm text-zinc-500">p50 per run</p>
                      </div>
                      <div>
                        <p className="text-3xl font-semibold">
                          {stats.p95Ms != null
                            ? `${(stats.p95Ms / 1000).toFixed(1)}s`
                            : "—"}
                        </p>
                        <p className="text-sm text-zinc-500">p95 per run</p>
                      </div>
                    </div>
                    <p className="mt-4 text-sm text-zinc-500">
                      {stats.slowestStep ? (
                        <>
                          Slowest step:{" "}
                          <span className="font-mono">
                            {stats.slowestStep.name}
                          </span>{" "}
                          ({(stats.slowestStep.avgMs / 1000).toFixed(1)}s avg).
                        </>
                      ) : (
                        "No duration data in spans yet."
                      )}
                    </p>
                  </Card>
                </div>

                <div className="mt-6 grid gap-6 md:grid-cols-2">
                  <Card title="Recent runs" hint="live from the API">
                    <ul className="divide-y divide-zinc-100">
                      {runs.slice(0, 8).map((r) => (
                        <li
                          key={r.traceId}
                          className="flex items-center justify-between py-3"
                        >
                          <div>
                            <p className="font-mono text-sm font-medium">{r.name}</p>
                            <p className="text-xs text-zinc-500">
                              {formatTokens(r.inputTokens + r.outputTokens)} tokens
                              ·{" "}
                              {r.durationMs != null
                                ? `${Math.round(r.durationMs)}ms`
                                : "no timing"}
                              · {r.spans} spans
                            </p>
                          </div>
                          <div className="text-right">
                            <p className="text-sm font-semibold">
                              {formatUsd(r.cost)}
                            </p>
                            <p
                              className={`text-xs ${
                                r.errors > 0
                                  ? "text-red-600"
                                  : "text-emerald-600"
                              }`}
                            >
                              {r.errors > 0 ? `${r.errors} errors` : "ok"}
                            </p>
                          </div>
                        </li>
                      ))}
                    </ul>
                  </Card>

                  <Card
                    title="Insights feed"
                    hint={
                      <button
                        onClick={handleRunInsights}
                        disabled={running}
                        className="rounded-full bg-zinc-900 px-3 py-1 text-xs font-medium text-white hover:bg-zinc-700 disabled:opacity-50"
                      >
                        {running ? "Running…" : "Run analysis"}
                      </button>
                    }
                  >
                    {!insights || insights.length === 0 ? (
                      <div className="rounded-xl bg-zinc-50 p-4 text-sm text-zinc-600">
                        <p className="font-medium text-zinc-800">
                          No insights yet.
                        </p>
                        <p className="mt-1">
                          Click “Run analysis” to execute the insight engine
                          over your recent spans — predictions and proposals
                          will appear here.
                        </p>
                      </div>
                    ) : (
                      <ul className="space-y-3">
                        {insights.map((i) => (
                          <li
                            key={i.id}
                            className="rounded-xl border border-zinc-100 bg-zinc-50 p-4"
                          >
                            <div className="flex items-center gap-2">
                              <span
                                className={`rounded-full px-2 py-0.5 text-xs font-medium ${severityColor(
                                  i.severity
                                )}`}
                              >
                                {typeLabel(i.type)}
                              </span>
                              <p className="text-sm font-semibold">{i.title}</p>
                            </div>
                            {i.detail && (
                              <p className="mt-2 text-sm text-zinc-600">{i.detail}</p>
                            )}
                            {i.suggested_action && (
                              <p className="mt-2 text-sm text-zinc-700">
                                <span className="font-medium">Suggested: </span>
                                {i.suggested_action}
                              </p>
                            )}
                          </li>
                        ))}
                      </ul>
                    )}
                  </Card>
                </div>
              </>
            )
          )}
        </>
      )}
    </main>
  );
}
