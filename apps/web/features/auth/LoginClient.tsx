"use client";

import { useState } from "react";
import Link from "next/link";
import { getSupabase, supabaseConfigured } from "@/lib/supabase";

export default function LoginClient() {
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  if (!supabaseConfigured()) {
    return (
      <main className="mx-auto max-w-md px-6 py-24 text-center">
        <Link href="/" className="text-lg font-semibold tracking-tight">
          Agentropy
        </Link>
        <div className="mt-8 rounded-2xl border border-amber-200 bg-amber-50 p-8">
          <h1 className="text-xl font-semibold text-amber-900">
            Sign-in isn&apos;t configured yet
          </h1>
          <p className="mt-3 text-sm text-amber-800">
            This deployment has no Supabase credentials. Set{" "}
            <span className="font-mono">NEXT_PUBLIC_SUPABASE_URL</span> and{" "}
            <span className="font-mono">NEXT_PUBLIC_SUPABASE_ANON_KEY</span>,
            then apply{" "}
            <span className="font-mono">supabase/migrations/001_init.sql</span>{" "}
            in your Supabase project.
          </p>
          <Link
            href="/dashboard"
            className="mt-6 inline-block rounded-full bg-zinc-900 px-6 py-2.5 text-sm font-medium text-white hover:bg-zinc-700"
          >
            Use the dashboard with an API key instead
          </Link>
        </div>
      </main>
    );
  }

  const sendLink = async () => {
    setError("");
    setBusy(true);
    try {
      const supabase = getSupabase()!;
      const { error } = await supabase.auth.signInWithOtp({
        email: email.trim(),
        options: { emailRedirectTo: `${window.location.origin}/dashboard` },
      });
      if (error) throw error;
      setSent(true);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not send magic link");
    } finally {
      setBusy(false);
    }
  };

  return (
    <main className="mx-auto max-w-md px-6 py-24">
      <div className="text-center">
        <Link href="/" className="text-lg font-semibold tracking-tight">
          Agentropy
        </Link>
        <h1 className="mt-6 text-2xl font-semibold tracking-tight">
          Log in with email
        </h1>
        <p className="mt-2 text-sm text-zinc-600">
          We&apos;ll send you a magic link — no password needed.
        </p>
      </div>
      {sent ? (
        <div className="mt-8 rounded-2xl border border-emerald-200 bg-emerald-50 p-6 text-center text-sm text-emerald-900">
          Check your inbox — the magic link is on its way.
        </div>
      ) : (
        <div className="mt-8 space-y-3">
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@company.com"
            className="w-full rounded-2xl border border-zinc-300 bg-white px-5 py-3 text-sm outline-none focus:border-zinc-500"
          />
          <button
            onClick={sendLink}
            disabled={busy || !email.trim()}
            className="w-full rounded-full bg-zinc-900 py-3 text-sm font-medium text-white hover:bg-zinc-700 disabled:opacity-50"
          >
            {busy ? "Sending…" : "Send magic link"}
          </button>
          {error && <p className="text-center text-sm text-red-600">{error}</p>}
        </div>
      )}
    </main>
  );
}
