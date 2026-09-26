import Link from "next/link";

function Card({
  title,
  children,
  hint,
}: {
  title: string;
  children: React.ReactNode;
  hint?: string;
}) {
  return (
    <section className="rounded-2xl border border-zinc-200 bg-white p-6">
      <div className="flex items-baseline justify-between">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-zinc-500">
          {title}
        </h2>
        {hint && <span className="text-xs text-zinc-400">{hint}</span>}
      </div>
      <div className="mt-4">{children}</div>
    </section>
  );
}

// TODO: replace with real data from GET /v1/traces on the FastAPI backend.
const sampleBars = [34, 52, 41, 68, 57, 80, 63];
const sampleTraces = [
  { id: "a1f9", name: "support-agent.run", tokens: "12.4k", cost: "$0.31", ms: 1840, status: "ok" },
  { id: "b2e8", name: "research-agent.run", tokens: "48.1k", cost: "$1.22", ms: 9200, status: "ok" },
  { id: "c3d7", name: "coder-agent.run", tokens: "96.7k", cost: "$2.05", ms: 21400, status: "slow" },
];

export default function DashboardPage() {
  return (
    <main className="mx-auto max-w-6xl px-6 py-10">
      <header className="flex items-center justify-between">
        <div>
          <Link href="/" className="text-lg font-semibold tracking-tight">
            Agentropy
          </Link>
          <p className="mt-1 text-sm text-zinc-500">
            What your agents did — and what to do about it.
          </p>
        </div>
        <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-medium text-amber-800">
          skeleton — sample data
        </span>
      </header>

      <div className="mt-8 grid gap-6 md:grid-cols-2">
        <Card title="Token usage & cost" hint="last 7 days">
          <div className="flex h-32 items-end gap-2">
            {sampleBars.map((h, i) => (
              <div
                key={i}
                className="flex-1 rounded-t bg-zinc-900"
                style={{ height: `${h}%`, opacity: 0.25 + (h / 100) * 0.75 }}
              />
            ))}
          </div>
          <div className="mt-3 flex justify-between text-sm">
            <span className="text-zinc-500">Total tokens</span>
            <span className="font-semibold">1.24M</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-zinc-500">Estimated cost</span>
            <span className="font-semibold">$18.42</span>
          </div>
        </Card>

        <Card title="Latency" hint="p50 / p95">
          <div className="flex items-end gap-8">
            <div>
              <p className="text-3xl font-semibold">2.1s</p>
              <p className="text-sm text-zinc-500">p50 per agent run</p>
            </div>
            <div>
              <p className="text-3xl font-semibold">9.4s</p>
              <p className="text-sm text-zinc-500">p95 per agent run</p>
            </div>
          </div>
          <p className="mt-4 text-sm text-zinc-500">
            {/* TODO: compute from real span durations once wired to the API. */}
            Slowest step in the selected period: tool call{" "}
            <span className="font-mono">web_search</span> (4.8s avg).
          </p>
        </Card>
      </div>

      <div className="mt-6 grid gap-6 md:grid-cols-2">
        <Card title="Recent traces" hint="from the API">
          {/* TODO: fetch GET /v1/traces from the FastAPI backend instead of this static sample. */}
          <ul className="divide-y divide-zinc-100">
            {sampleTraces.map((t) => (
              <li key={t.id} className="flex items-center justify-between py-3">
                <div>
                  <p className="font-mono text-sm font-medium">{t.name}</p>
                  <p className="text-xs text-zinc-500">
                    {t.tokens} tokens · {t.ms}ms
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-semibold">{t.cost}</p>
                  <p
                    className={`text-xs ${
                      t.status === "ok" ? "text-emerald-600" : "text-amber-600"
                    }`}
                  >
                    {t.status}
                  </p>
                </div>
              </li>
            ))}
          </ul>
        </Card>

        <Card title="Insights feed" hint="AI engine">
          <div className="rounded-xl bg-zinc-50 p-4 text-sm text-zinc-600">
            <p className="font-medium text-zinc-800">
              The insight engine is not implemented yet.
            </p>
            <p className="mt-1">
              {/* TODO: predictions and improvement proposals will appear here once the insight agent ships. */}
              This is where predictions (cost, latency, failures) and concrete
              improvement proposals will show up — the core of the product.
            </p>
          </div>
        </Card>
      </div>
    </main>
  );
}
