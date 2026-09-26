"use client";

import { useState } from "react";
import Link from "next/link";
import { createCheckout } from "@/lib/api";
import { getSupabase } from "@/lib/supabase";

const PLANS = [
  {
    tier: "starter" as const,
    name: "Starter",
    price: "$19",
    blurb: "For solo builders shipping their first agents.",
    features: [
      "Unlimited seats",
      "Full insight engine (predictions + proposals)",
      "Standard OTel capture",
      "14-day full trial",
    ],
  },
  {
    tier: "pro" as const,
    name: "Pro",
    price: "$49",
    blurb: "For teams running agents in production.",
    features: [
      "Everything in Starter",
      "Unlimited seats",
      "Higher ingest volume & longer retention",
      "Priority support",
      "14-day full trial",
    ],
    highlighted: true,
  },
];

export default function PricingClient() {
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState("");

  const subscribe = async (tier: "starter" | "pro") => {
    setError("");
    const supabase = getSupabase();
    if (!supabase) {
      setError(
        "Accounts aren't configured yet (Supabase). Billing will be available once sign-in is live."
      );
      return;
    }
    const {
      data: { session },
    } = await supabase.auth.getSession();
    if (!session) {
      window.location.href = "/login?next=/pricing";
      return;
    }
    setBusy(tier);
    try {
      const { checkout_url } = await createCheckout(tier, session.access_token);
      window.location.href = checkout_url;
    } catch (e) {
      setError(e instanceof Error ? e.message : "Checkout failed");
    } finally {
      setBusy(null);
    }
  };

  return (
    <main className="mx-auto max-w-6xl px-6 py-16">
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

      <div className="mx-auto mt-16 max-w-2xl text-center">
        <p className="text-sm font-medium uppercase tracking-widest text-zinc-400">
          Pricing
        </p>
        <h1 className="mt-3 text-4xl font-semibold tracking-tight">
          Indie pricing. Unlimited seats.
        </h1>
        <p className="mt-4 text-lg text-zinc-600">
          No per-seat tax, no surprise overages. Every plan includes the full
          insight engine and starts with a 14-day trial.
        </p>
      </div>

      {error && (
        <div className="mx-auto mt-8 max-w-2xl rounded-2xl border border-amber-200 bg-amber-50 p-5 text-sm text-amber-900">
          {error}
        </div>
      )}

      <div className="mx-auto mt-12 grid max-w-4xl gap-6 md:grid-cols-2">
        {PLANS.map((p) => (
          <div
            key={p.tier}
            className={`rounded-3xl border p-8 ${
              p.highlighted
                ? "border-zinc-900 bg-zinc-900 text-white"
                : "border-zinc-200 bg-white"
            }`}
          >
            <h2 className="text-lg font-semibold">{p.name}</h2>
            <p className={`mt-1 text-sm ${p.highlighted ? "text-zinc-400" : "text-zinc-500"}`}>
              {p.blurb}
            </p>
            <p className="mt-6">
              <span className="text-5xl font-semibold">{p.price}</span>
              <span className={p.highlighted ? "text-zinc-400" : "text-zinc-500"}>
                /month
              </span>
            </p>
            <ul className="mt-6 space-y-3 text-sm">
              {p.features.map((f) => (
                <li key={f} className="flex items-start gap-2">
                  <span aria-hidden>✓</span>
                  <span className={p.highlighted ? "text-zinc-300" : "text-zinc-600"}>
                    {f}
                  </span>
                </li>
              ))}
            </ul>
            <button
              onClick={() => subscribe(p.tier)}
              disabled={busy !== null}
              className={`mt-8 w-full rounded-full py-3 text-sm font-medium disabled:opacity-50 ${
                p.highlighted
                  ? "bg-white text-zinc-900 hover:bg-zinc-200"
                  : "bg-zinc-900 text-white hover:bg-zinc-700"
              }`}
            >
              {busy === p.tier ? "Redirecting…" : `Start 14-day trial — ${p.name}`}
            </button>
          </div>
        ))}
      </div>

      <p className="mx-auto mt-10 max-w-2xl text-center text-sm text-zinc-500">
        Payments are processed securely by Polar. Cancel anytime; your data
        stays exportable because capture is standard OpenTelemetry.
      </p>
    </main>
  );
}
