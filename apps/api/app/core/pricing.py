"""Approximate per-model token pricing (USD per 1M tokens, input/output).

Used for cost estimates in the dashboard and the insight engine. These are
rough public list-price approximations — never use them for billing.
TODO: refresh periodically and/or let workspaces set custom rates.
"""

from __future__ import annotations

# (input_per_1m, output_per_1m)
_PRICES: dict[str, tuple[float, float]] = {
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4o": (2.50, 10.00),
    "gpt-4.1-mini": (0.40, 1.60),
    "gpt-4.1": (2.00, 8.00),
    "o4-mini": (1.10, 4.40),
    "claude-opus-4-6": (15.00, 75.00),
    "claude-sonnet-4-6": (3.00, 15.00),
    "claude-haiku": (0.80, 4.00),
    "gemini-2.0-flash": (0.10, 0.40),
    "gemini-2.5-pro": (1.25, 10.00),
}

_DEFAULT = (2.00, 8.00)


def _normalize(model: str) -> str:
    return (model or "").strip().lower()


def price_for(model: str) -> tuple[float, float]:
    name = _normalize(model)
    if name in _PRICES:
        return _PRICES[name]
    # prefix fallback, e.g. "gpt-4o-2024-11-20" -> "gpt-4o"
    for key, price in _PRICES.items():
        if name.startswith(key):
            return price
    return _DEFAULT


def estimate_cost(input_tokens: int, output_tokens: int, model: str) -> float:
    in_price, out_price = price_for(model)
    return (input_tokens * in_price + output_tokens * out_price) / 1_000_000
