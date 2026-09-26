import Link from "next/link";

const pillars = [
  {
    title: "One-prompt setup",
    body: "Describe what you want to observe in a single prompt. Your coding agent generates the instrumentation — observability in one shot.",
  },
  {
    title: "Everything that matters",
    body: "Token usage and cost, latency, agent context, tool calls, errors and full trajectories. Standard OpenTelemetry capture, nothing proprietary.",
  },
  {
    title: "Insights, not just traces",
    body: "An AI engine that predicts cost, latency and failures — and proposes concrete improvements based on what it observed.",
  },
];

export default function LandingPage() {
  return (
    <main className="mx-auto max-w-5xl px-6 py-20">
      <header className="flex items-center justify-between">
        <span className="text-lg font-semibold tracking-tight">
          Agentropy
        </span>
        <Link
          href="/dashboard"
          className="rounded-full bg-zinc-900 px-5 py-2 text-sm font-medium text-white hover:bg-zinc-700"
        >
          Open dashboard
        </Link>
      </header>

      <section className="mt-24 text-center">
        <p className="text-sm font-medium uppercase tracking-widest text-zinc-400">
          See it. Improve it.
        </p>
        <h1 className="mx-auto mt-4 max-w-3xl text-5xl font-semibold leading-tight tracking-tight">
          Agent observability,
          <br />
          minus the noise.
        </h1>
        <p className="mx-auto mt-6 max-w-xl text-lg text-zinc-600">
          We don&apos;t bury you in traces. We tell you what your agents cost,
          what will break, and what to fix — simply and beautifully.
        </p>
        <div className="mt-10 flex items-center justify-center gap-4">
          <Link
            href="/dashboard"
            className="rounded-full bg-zinc-900 px-7 py-3 text-sm font-medium text-white hover:bg-zinc-700"
          >
            See the dashboard
          </Link>
          <span className="rounded-full border border-zinc-300 px-5 py-3 font-mono text-sm text-zinc-600">
            pip install agentropy
          </span>
        </div>
      </section>

      <section className="mt-24 grid gap-6 md:grid-cols-3">
        {pillars.map((p) => (
          <div
            key={p.title}
            className="rounded-2xl border border-zinc-200 bg-white p-6"
          >
            <h2 className="text-base font-semibold">{p.title}</h2>
            <p className="mt-2 text-sm leading-relaxed text-zinc-600">{p.body}</p>
          </div>
        ))}
      </section>

      <footer className="mt-24 border-t border-zinc-200 pt-8 text-center text-sm text-zinc-500">
        Agentropy — open-core agent observability. Capture is open source;
        the insight engine is the product.
      </footer>
    </main>
  );
}
