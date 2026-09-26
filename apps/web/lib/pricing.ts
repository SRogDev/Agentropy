/** Approximate per-model token pricing (USD per 1M tokens).
 * Mirrors apps/api/app/core/pricing.py — estimates only, never for billing.
 */
const PRICES: Record<string, [number, number]> = {
  "gpt-4o-mini": [0.15, 0.6],
  "gpt-4o": [2.5, 10.0],
  "gpt-4.1-mini": [0.4, 1.6],
  "gpt-4.1": [2.0, 8.0],
  "o4-mini": [1.1, 4.4],
  "claude-opus-4-6": [15.0, 75.0],
  "claude-sonnet-4-6": [3.0, 15.0],
  "claude-haiku": [0.8, 4.0],
  "gemini-2.0-flash": [0.1, 0.4],
  "gemini-2.5-pro": [1.25, 10.0],
};

const DEFAULT: [number, number] = [2.0, 8.0];

export function estimateCost(
  inputTokens: number,
  outputTokens: number,
  model: string
): number {
  const name = (model || "").toLowerCase();
  let price = DEFAULT;
  if (PRICES[name]) price = PRICES[name];
  else {
    for (const key of Object.keys(PRICES)) {
      if (name.startsWith(key)) {
        price = PRICES[key];
        break;
      }
    }
  }
  return (inputTokens * price[0] + outputTokens * price[1]) / 1_000_000;
}

export function formatTokens(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(2)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}k`;
  return `${n}`;
}

export function formatUsd(n: number): string {
  return `$${n.toFixed(n < 1 ? 4 : 2)}`;
}
