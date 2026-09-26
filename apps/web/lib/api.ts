/** API client for the Agentropy FastAPI backend. */

export function apiBase(): string {
  return (
    process.env.NEXT_PUBLIC_AGENTROPY_API_URL || "http://localhost:8000"
  ).replace(/\/$/, "");
}

export interface Span {
  trace_id: string;
  span_id: string;
  name: string;
  attributes: Record<string, unknown>;
  duration_ms: number | null;
  is_error: boolean;
  received_at: number;
}

export interface Insight {
  id: number | null;
  type: "prediction" | "warning" | "proposal";
  severity: "info" | "low" | "medium" | "high";
  title: string;
  detail: string;
  suggested_action: string;
  data: Record<string, unknown>;
  created_at: number | null;
}

async function authed(path: string, apiKey: string, init?: RequestInit) {
  const res = await fetch(`${apiBase()}${path}`, {
    ...init,
    headers: { "X-API-Key": apiKey, ...(init?.headers || {}) },
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`API ${res.status}: ${text || res.statusText}`);
  }
  return res.json();
}

export function fetchTraces(apiKey: string, limit = 500) {
  return authed(`/v1/traces?limit=${limit}`, apiKey) as Promise<{
    spans: Span[];
  }>;
}

export function fetchInsights(apiKey: string, limit = 20) {
  return authed(`/v1/insights?limit=${limit}`, apiKey) as Promise<{
    insights: Insight[];
  }>;
}

export function runInsights(apiKey: string) {
  return authed(`/v1/insights/run`, apiKey, { method: "POST" }) as Promise<
    Insight[]
  >;
}

export async function createCheckout(
  tier: "starter" | "pro",
  jwt: string
): Promise<{ checkout_url: string }> {
  const res = await fetch(`${apiBase()}/v1/billing/checkout`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${jwt}`,
    },
    body: JSON.stringify({ tier }),
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(
      res.status === 503
        ? "Billing is not configured yet."
        : `Checkout failed (${res.status}): ${text || res.statusText}`
    );
  }
  return res.json();
}
