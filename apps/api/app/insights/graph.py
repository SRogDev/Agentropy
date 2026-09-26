"""The insight engine — a LangGraph StateGraph.

This is the product's differentiator: it turns observed spans into
predictions and concrete improvement proposals.

Pipeline:
    load_traces -> compute_stats -> forecast -> detect_issues -> propose -> persist

- Rules are the default and always run (no LLM needed).
- If OPENROUTER_API_KEY is set, `propose` optionally asks an LLM (via
  OpenRouter, mid-tier model from OPENROUTER_MODEL) to tighten the
  wording of each insight. The facts (numbers, thresholds) always come from
  the rules — the LLM only polishes prose, and failures fall back to rules.

TODO: run on a schedule (cron/worker) instead of only on demand via
POST /v1/insights/run.
TODO: per-workspace scoping once multi-tenancy lands (currently global).
"""

from __future__ import annotations

import math
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from ..core import metrics_store
from ..core.config import settings
from ..core.pricing import estimate_cost


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------


class InsightState(TypedDict, total=False):
    spans: list[dict[str, Any]]
    stats: dict[str, Any]
    forecasts: list[dict[str, Any]]
    issues: list[dict[str, Any]]
    insights: list[dict[str, Any]]
    persisted_ids: list[int]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _percentile(values: list[float], pct: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    k = (len(ordered) - 1) * (pct / 100)
    lo, hi = math.floor(k), math.ceil(k)
    if lo == hi:
        return ordered[int(k)]
    return ordered[lo] + (ordered[hi] - ordered[lo]) * (k - lo)


def _agent_of(span: dict[str, Any]) -> str:
    attrs = span.get("attributes", {})
    return (
        attrs.get("agent.name")
        or attrs.get("service.name")
        or attrs.get("service_name")
        or "unknown-agent"
    )


def _model_of(span: dict[str, Any]) -> str:
    return span.get("attributes", {}).get("gen_ai.request.model", "unknown-model")


def _linreg(xs: list[float], ys: list[float]) -> tuple[float, float]:
    """Least-squares slope/intercept. Flat line when underspecified."""
    n = len(xs)
    if n < 2:
        return 0.0, ys[0] if ys else 0.0
    mx, my = sum(xs) / n, sum(ys) / n
    denom = sum((x - mx) ** 2 for x in xs)
    if denom == 0:
        return 0.0, my
    slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / denom
    return slope, my - slope * mx


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------


def load_traces(state: InsightState) -> dict[str, Any]:
    # TODO: per-workspace scoping; configurable lookback window.
    spans = metrics_store.recent_spans(limit=2000)
    return {"spans": spans}


def compute_stats(state: InsightState) -> dict[str, Any]:
    spans = state.get("spans", [])
    runs: dict[str, list[dict[str, Any]]] = {}
    for s in spans:
        runs.setdefault(s["trace_id"], []).append(s)

    per_agent: dict[str, dict[str, float]] = {}
    agent_traces: dict[str, set[str]] = {}
    run_costs: list[float] = []
    run_latencies: list[float] = []
    run_input_tokens: list[float] = []
    error_spans = 0
    tool_failures: dict[str, int] = {}
    tool_totals: dict[str, int] = {}
    daily: dict[int, dict[str, Any]] = {}

    for trace_id, trace_spans in runs.items():
        in_tok = out_tok = 0
        cost = 0.0
        for s in trace_spans:
            attrs = s.get("attributes", {})
            it = int(attrs.get("gen_ai.usage.input_tokens", 0) or 0)
            ot = int(attrs.get("gen_ai.usage.output_tokens", 0) or 0)
            in_tok += it
            out_tok += ot
            cost += estimate_cost(it, ot, _model_of(s))
            agent = _agent_of(s)
            agent_traces.setdefault(agent, set()).add(trace_id)
            agg = per_agent.setdefault(
                agent, {"input_tokens": 0, "output_tokens": 0, "cost": 0.0, "runs": 0}
            )
            agg["input_tokens"] += it
            agg["output_tokens"] += ot
            agg["cost"] += estimate_cost(it, ot, _model_of(s))
            if s.get("is_error"):
                error_spans += 1
            tool = attrs.get("tool.name")
            if tool:
                tool_totals[tool] = tool_totals.get(tool, 0) + 1
                if s.get("is_error"):
                    tool_failures[tool] = tool_failures.get(tool, 0) + 1
        run_costs.append(cost)
        run_input_tokens.append(float(in_tok))
        durations = [s["duration_ms"] for s in trace_spans if s.get("duration_ms")]
        if durations:
            run_latencies.append(max(durations))
        day = int(min(s["received_at"] for s in trace_spans) // 86400)
        bucket = daily.setdefault(
            day, {"cost": 0.0, "runs": 0, "latencies": [], "errors": 0, "spans": 0}
        )
        bucket["cost"] += cost
        bucket["runs"] += 1
        bucket["latencies"].extend(durations)
        bucket["spans"] += len(trace_spans)
        bucket["errors"] += sum(1 for s in trace_spans if s.get("is_error"))

    for agent, traces in agent_traces.items():
        per_agent[agent]["runs"] = len(traces)

    total_spans = len(spans)
    stats = {
        "runs": len(runs),
        "total_spans": total_spans,
        "total_cost": round(sum(run_costs), 4),
        "total_input_tokens": sum(
            int(v) for v in [a["input_tokens"] for a in per_agent.values()]
        ),
        "total_output_tokens": sum(
            int(v) for v in [a["output_tokens"] for a in per_agent.values()]
        ),
        "avg_cost_per_run": round(sum(run_costs) / len(run_costs), 4) if run_costs else 0,
        "avg_input_tokens_per_run": (
            round(sum(run_input_tokens) / len(run_input_tokens), 1)
            if run_input_tokens
            else 0
        ),
        "p50_latency_ms": _percentile(run_latencies, 50),
        "p95_latency_ms": _percentile(run_latencies, 95),
        "error_rate": round(error_spans / total_spans, 4) if total_spans else 0,
        "per_agent": per_agent,
        "tool_failures": tool_failures,
        "tool_totals": tool_totals,
        "daily": {
            str(day): {
                "cost": round(b["cost"], 4),
                "runs": b["runs"],
                "p95_latency_ms": _percentile(b["latencies"], 95),
                "error_rate": round(b["errors"] / b["spans"], 4) if b["spans"] else 0,
            }
            for day, b in sorted(daily.items())
        },
    }
    return {"stats": stats}


def forecast(state: InsightState) -> dict[str, Any]:
    """Naive but real projections: linear trend on daily cost and p95 latency."""
    stats = state.get("stats", {})
    daily = stats.get("daily", {})
    days = sorted(int(d) for d in daily)
    forecasts: list[dict[str, Any]] = []

    def project(key: str, unit: str, label: str) -> None:
        ys = [daily[str(d)][key] or 0 for d in days]
        xs = list(range(len(days)))
        slope, intercept = _linreg([float(x) for x in xs], [float(y) for y in ys])
        current = ys[-1] if ys else 0
        proj_7 = max(0.0, intercept + slope * (len(days) - 1 + 7))
        proj_30 = max(0.0, intercept + slope * (len(days) - 1 + 30))
        if len(days) < 2:
            trend = "flat"
            note = "Only one day of data — projection assumes today repeats."
        elif slope > 0.05 * max(current, 1e-9):
            trend = "up"
            note = ""
        elif slope < -0.05 * max(current, 1e-9):
            trend = "down"
            note = ""
        else:
            trend = "flat"
            note = ""
        forecasts.append(
            {
                "metric": label,
                "unit": unit,
                "current_daily": round(current, 4),
                "projected_7d_daily": round(proj_7, 4),
                "projected_30d_daily": round(proj_30, 4),
                "trend": trend,
                "note": note,
                "days_of_history": len(days),
            }
        )

    if days:
        project("cost", "USD/day", "daily cost")
        project("p95_latency_ms", "ms", "p95 run latency")
    return {"forecasts": forecasts}


def detect_issues(state: InsightState) -> dict[str, Any]:
    """Rule-based anomaly detection: recent window vs baseline."""
    stats = state.get("stats", {})
    spans = state.get("spans", [])
    issues: list[dict[str, Any]] = []
    if stats.get("runs", 0) < 2:
        issues.append(
            {
                "kind": "thin_data",
                "severity": "info",
                "title": "Not enough history yet",
                "detail": (
                    f"Only {stats.get('runs', 0)} agent run(s) observed. "
                    "Predictions sharpen as you send more runs; keep the SDK running."
                ),
                "data": {"runs": stats.get("runs", 0)},
            }
        )
        return {"issues": issues}

    # Split runs into baseline (older 70%) vs recent (newest 30%).
    by_trace: dict[str, list[dict[str, Any]]] = {}
    for s in spans:
        by_trace.setdefault(s["trace_id"], []).append(s)
    ordered = sorted(
        by_trace.items(), key=lambda kv: min(s["received_at"] for s in kv[1])
    )
    cut = max(1, int(len(ordered) * 0.7))
    baseline_traces = [t for _, t in ordered[:cut]]
    recent_traces = [t for _, t in ordered[cut:]] or [t for _, t in ordered[-1:]]

    def window_stats(traces: list[list[dict[str, Any]]]) -> dict[str, float]:
        costs, lats, in_toks, errs, total = [], [], [], 0, 0
        for trace in traces:
            c = 0.0
            it = 0
            for s in trace:
                attrs = s.get("attributes", {})
                i = int(attrs.get("gen_ai.usage.input_tokens", 0) or 0)
                o = int(attrs.get("gen_ai.usage.output_tokens", 0) or 0)
                it += i
                c += estimate_cost(i, o, _model_of(s))
                total += 1
                if s.get("is_error"):
                    errs += 1
            costs.append(c)
            in_toks.append(float(it))
            durs = [s["duration_ms"] for s in trace if s.get("duration_ms")]
            if durs:
                lats.append(max(durs))
        return {
            "avg_cost": sum(costs) / len(costs) if costs else 0,
            "p95_lat": _percentile(lats, 95) or 0,
            "avg_in_tok": sum(in_toks) / len(in_toks) if in_toks else 0,
            "err_rate": errs / total if total else 0,
            "n": len(traces),
        }

    base = window_stats(baseline_traces)
    recent = window_stats(recent_traces)

    if recent["err_rate"] > max(2 * base["err_rate"], 0.05) and recent["n"] >= 2:
        issues.append(
            {
                "kind": "error_rate_spike",
                "severity": "high",
                "title": "Error rate spiking",
                "detail": (
                    f"Error rate in recent runs is {recent['err_rate']:.1%} vs "
                    f"{base['err_rate']:.1%} baseline."
                ),
                "data": {"recent": recent["err_rate"], "baseline": base["err_rate"]},
            }
        )
    if base["p95_lat"] and recent["p95_lat"] > 1.5 * base["p95_lat"]:
        issues.append(
            {
                "kind": "latency_regression",
                "severity": "medium",
                "title": "p95 latency regressing",
                "detail": (
                    f"Recent p95 latency {recent['p95_lat']:.0f}ms vs "
                    f"{base['p95_lat']:.0f}ms baseline."
                ),
                "data": {"recent": recent["p95_lat"], "baseline": base["p95_lat"]},
            }
        )
    if base["avg_cost"] and recent["avg_cost"] > 1.3 * base["avg_cost"]:
        issues.append(
            {
                "kind": "cost_growth",
                "severity": "medium",
                "title": "Cost per run growing",
                "detail": (
                    f"Average cost per run is ${recent['avg_cost']:.4f} vs "
                    f"${base['avg_cost']:.4f} baseline."
                ),
                "data": {"recent": recent["avg_cost"], "baseline": base["avg_cost"]},
            }
        )
    if base["avg_in_tok"] and recent["avg_in_tok"] > 1.3 * base["avg_in_tok"]:
        issues.append(
            {
                "kind": "token_bloat",
                "severity": "low",
                "title": "Input tokens creeping up",
                "detail": (
                    f"Average input tokens per run: {recent['avg_in_tok']:.0f} vs "
                    f"{base['avg_in_tok']:.0f} baseline. Context may be accumulating."
                ),
                "data": {"recent": recent["avg_in_tok"], "baseline": base["avg_in_tok"]},
            }
        )

    # Repeated identical tool failures (across all spans, not just recent).
    for tool, fails in (stats.get("tool_failures") or {}).items():
        if fails >= 3:
            issues.append(
                {
                    "kind": "tool_failures",
                    "severity": "high",
                    "title": f"Tool '{tool}' keeps failing",
                    "detail": (
                        f"{fails} failed calls out of "
                        f"{(stats.get('tool_totals') or {}).get(tool, '?')} total."
                    ),
                    "data": {"tool": tool, "failures": fails},
                }
            )
    return {"issues": issues}


_SUGGESTED_ACTIONS: dict[str, str] = {
    "error_rate_spike": (
        "Inspect the failing traces, add retries with backoff around the failing "
        "step, and consider a fallback model or degraded mode."
    ),
    "latency_regression": (
        "Profile the slowest spans in the recent traces; parallelize independent "
        "tool calls and cap per-step timeouts."
    ),
    "cost_growth": (
        "Check which model/prompt grew: route simple steps to a cheaper model, "
        "trim system prompts, and cache repeated context."
    ),
    "token_bloat": (
        "Summarize or truncate conversation history and retrieved context before "
        "each LLM call; set a max input-token budget per run."
    ),
    "tool_failures": (
        "Fix or add retries/timeouts for the failing tool; log its inputs so the "
        "next failure is debuggable from the trace."
    ),
    "thin_data": (
        "No action needed — keep instrumented traffic flowing and re-run insights."
    ),
}


def _maybe_refine_with_llm(insights: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Optionally polish wording with an LLM. Facts stay rule-generated;
    any failure silently falls back to the rule text."""
    if not settings.openrouter_api_key or not insights:
        return insights
    try:
        import httpx

        lines = "\n".join(
            f"- [{i['type']}/{i['severity']}] {i['title']}: {i['detail']}"
            for i in insights
        )
        resp = httpx.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.openrouter_api_key}",
                "HTTP-Referer": "https://agentropy.dev",
                "X-Title": "Agentropy Insight Engine",
            },
            json={
                "model": settings.openrouter_model,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You polish observability insight titles and details. "
                            "Keep every number and fact identical; only improve "
                            "clarity and tone. Reply with the same list, one line "
                            "per insight, format: TITLE || DETAIL"
                        ),
                    },
                    {"role": "user", "content": lines},
                ],
                "temperature": 0.2,
            },
            timeout=20,
        )
        text = resp.json()["choices"][0]["message"]["content"]
        for line, insight in zip(text.strip().split("\n"), insights):
            if "||" in line:
                title, detail = line.split("||", 1)
                insight["title"] = title.strip("- ").strip()
                insight["detail"] = detail.strip()
    except Exception:
        pass  # honest fallback: rule-generated wording stands
    return insights


def propose(state: InsightState) -> dict[str, Any]:
    insights: list[dict[str, Any]] = []
    for issue in state.get("issues", []):
        kind = issue["kind"]
        itype = "warning" if issue["severity"] in ("high", "medium") else "proposal"
        if kind == "thin_data":
            itype = "prediction"  # honest: prediction about needing more data
        insights.append(
            {
                "type": itype,
                "severity": issue["severity"],
                "title": issue["title"],
                "detail": issue["detail"],
                "suggested_action": _SUGGESTED_ACTIONS.get(kind, ""),
                "data": {"kind": kind, **issue.get("data", {})},
            }
        )
    for fc in state.get("forecasts", []):
        if fc["trend"] == "up":
            insights.append(
                {
                    "type": "prediction",
                    "severity": "medium",
                    "title": f"{fc['metric'].capitalize()} trending up",
                    "detail": (
                        f"Currently {fc['current_daily']}{fc['unit']}; linear trend "
                        f"projects {fc['projected_7d_daily']}{fc['unit']} in 7 days "
                        f"and {fc['projected_30d_daily']}{fc['unit']} in 30 days "
                        f"(based on {fc['days_of_history']} day(s) of history)."
                    ),
                    "suggested_action": (
                        "Act before it compounds: find the step driving the trend "
                        "in the traces and apply the cheapest fix first."
                    ),
                    "data": {"forecast": fc},
                }
            )
        else:
            insights.append(
                {
                    "type": "prediction",
                    "severity": "info",
                    "title": f"{fc['metric'].capitalize()} forecast ({fc['trend']})",
                    "detail": (
                        f"Currently {fc['current_daily']}{fc['unit']}; projected "
                        f"{fc['projected_7d_daily']}{fc['unit']}/day in 7 days "
                        f"({fc['days_of_history']} day(s) of history). "
                        f"{fc['note']}".strip()
                    ),
                    "suggested_action": "",
                    "data": {"forecast": fc},
                }
            )
    insights = _maybe_refine_with_llm(insights)
    return {"insights": insights}


def persist(state: InsightState) -> dict[str, Any]:
    ids = [metrics_store.store_insight(i) for i in state.get("insights", [])]
    return {"persisted_ids": ids}


def build_graph():
    graph = StateGraph(InsightState)
    graph.add_node("load_traces", load_traces)
    graph.add_node("compute_stats", compute_stats)
    graph.add_node("forecast", forecast)
    graph.add_node("detect_issues", detect_issues)
    graph.add_node("propose", propose)
    graph.add_node("persist", persist)
    graph.add_edge(START, "load_traces")
    graph.add_edge("load_traces", "compute_stats")
    graph.add_edge("compute_stats", "forecast")
    graph.add_edge("forecast", "detect_issues")
    graph.add_edge("detect_issues", "propose")
    graph.add_edge("propose", "persist")
    graph.add_edge("persist", END)
    return graph.compile()
