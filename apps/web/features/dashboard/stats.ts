/** Dashboard data computation from real API spans. */
import { estimateCost, formatTokens, formatUsd } from "@/lib/pricing";
import type { Span } from "@/lib/api";

export interface RunSummary {
  traceId: string;
  name: string;
  inputTokens: number;
  outputTokens: number;
  cost: number;
  durationMs: number | null;
  errors: number;
  spans: number;
  receivedAt: number;
}

export interface DashboardStats {
  runs: number;
  totalInput: number;
  totalOutput: number;
  totalCost: number;
  p50Ms: number | null;
  p95Ms: number | null;
  errorRate: number;
  slowestStep: { name: string; avgMs: number } | null;
}

function percentile(values: number[], pct: number): number | null {
  if (!values.length) return null;
  const ordered = [...values].sort((a, b) => a - b);
  const k = (ordered.length - 1) * (pct / 100);
  const lo = Math.floor(k);
  const hi = Math.ceil(k);
  return lo === hi
    ? ordered[k]
    : ordered[lo] + (ordered[hi] - ordered[lo]) * (k - lo);
}

function numAttr(attrs: Record<string, unknown>, key: string): number {
  const v = attrs[key];
  const n = typeof v === "string" ? parseInt(v, 10) : (v as number);
  return Number.isFinite(n) ? n : 0;
}

function strAttr(attrs: Record<string, unknown>, key: string): string {
  const v = attrs[key];
  return typeof v === "string" ? v : "";
}

function agentName(span: Span): string {
  const a = span.attributes;
  return (
    strAttr(a, "agent.name") ||
    strAttr(a, "service.name") ||
    "unknown-agent"
  );
}

export function summarizeRuns(spans: Span[]): RunSummary[] {
  const byTrace = new Map<string, Span[]>();
  for (const s of spans) {
    const list = byTrace.get(s.trace_id) || [];
    list.push(s);
    byTrace.set(s.trace_id, list);
  }
  const runs: RunSummary[] = [];
  for (const [traceId, traceSpans] of byTrace) {
    let input = 0;
    let output = 0;
    let cost = 0;
    let errors = 0;
    let maxDur: number | null = null;
    let name = "";
    let receivedAt = 0;
    for (const s of traceSpans) {
      const it = numAttr(s.attributes, "gen_ai.usage.input_tokens");
      const ot = numAttr(s.attributes, "gen_ai.usage.output_tokens");
      const model = strAttr(s.attributes, "gen_ai.request.model");
      input += it;
      output += ot;
      cost += estimateCost(it, ot, model);
      if (s.is_error) errors++;
      if (s.duration_ms != null)
        maxDur = maxDur == null ? s.duration_ms : Math.max(maxDur, s.duration_ms);
      if (!name && s.name.endsWith(".run")) name = s.name;
      receivedAt = Math.max(receivedAt, s.received_at);
    }
    if (!name) name = `${agentName(traceSpans[0])}.run`;
    runs.push({
      traceId,
      name,
      inputTokens: input,
      outputTokens: output,
      cost,
      durationMs: maxDur,
      errors,
      spans: traceSpans.length,
      receivedAt,
    });
  }
  return runs.sort((a, b) => b.receivedAt - a.receivedAt);
}

export function computeStats(runs: RunSummary[], spans: Span[]): DashboardStats {
  const durations = runs
    .map((r) => r.durationMs)
    .filter((d): d is number => d != null);
  const errorSpans = spans.filter((s) => s.is_error).length;

  // Slowest step: average duration by span name (excluding *.run roots).
  const byName = new Map<string, number[]>();
  for (const s of spans) {
    if (s.duration_ms == null || s.name.endsWith(".run")) continue;
    const list = byName.get(s.name) || [];
    list.push(s.duration_ms);
    byName.set(s.name, list);
  }
  let slowestStep: DashboardStats["slowestStep"] = null;
  for (const [name, ds] of byName) {
    const avg = ds.reduce((a, b) => a + b, 0) / ds.length;
    if (!slowestStep || avg > slowestStep.avgMs) slowestStep = { name, avgMs: avg };
  }

  return {
    runs: runs.length,
    totalInput: runs.reduce((a, r) => a + r.inputTokens, 0),
    totalOutput: runs.reduce((a, r) => a + r.outputTokens, 0),
    totalCost: runs.reduce((a, r) => a + r.cost, 0),
    p50Ms: percentile(durations, 50),
    p95Ms: percentile(durations, 95),
    errorRate: spans.length ? errorSpans / spans.length : 0,
    slowestStep,
  };
}

export { formatTokens, formatUsd };
