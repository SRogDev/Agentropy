import Link from "next/link";

export function LandingNav() {
  return (
    <header className="mx-auto flex max-w-6xl items-center justify-between px-6 py-6">
      <Link href="/" className="text-lg font-semibold tracking-tight">
        Agentropy
      </Link>
      <nav className="hidden items-center gap-8 text-sm text-zinc-600 md:flex">
        <Link href="#how" className="hover:text-zinc-900">
          How it works
        </Link>
        <Link href="#features" className="hover:text-zinc-900">
          Features
        </Link>
        <Link href="#compare" className="hover:text-zinc-900">
          Compare
        </Link>
        <Link href="/pricing" className="hover:text-zinc-900">
          Pricing
        </Link>
        <Link href="/docs" className="hover:text-zinc-900">
          Docs
        </Link>
      </nav>
      <div className="flex items-center gap-3">
        <Link
          href="/login"
          className="text-sm font-medium text-zinc-600 hover:text-zinc-900"
        >
          Log in
        </Link>
        <Link
          href="/dashboard"
          className="rounded-full bg-zinc-900 px-5 py-2 text-sm font-medium text-white hover:bg-zinc-700"
        >
          Open dashboard
        </Link>
      </div>
    </header>
  );
}

export function Hero() {
  return (
    <section className="mx-auto max-w-6xl px-6 pb-20 pt-16 text-center md:pt-24">
      <p className="text-sm font-medium uppercase tracking-widest text-zinc-400">
        See it. Improve it.
      </p>
      <h1 className="mx-auto mt-4 max-w-3xl text-5xl font-semibold leading-tight tracking-tight md:text-6xl">
        Agent observability,
        <br />
        minus the noise.
      </h1>
      <p className="mx-auto mt-6 max-w-xl text-lg text-zinc-600">
        Your agents burn money and fail silently. Other tools hand you 10,000
        traces and zero answers. Agentropy tells you what your agents cost,
        what will break, and exactly what to fix.
      </p>
      <div className="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row">
        <Link
          href="/dashboard"
          className="rounded-full bg-zinc-900 px-7 py-3 text-sm font-medium text-white hover:bg-zinc-700"
        >
          See the dashboard
        </Link>
        <Link
          href="/docs"
          className="rounded-full border border-zinc-300 px-7 py-3 font-mono text-sm text-zinc-700 hover:border-zinc-500"
        >
          pip install agentropy
        </Link>
      </div>
      <p className="mt-6 text-sm text-zinc-500">
        One-prompt setup · Unlimited seats · From $19/mo
      </p>
    </section>
  );
}

export function Problem() {
  return (
    <section className="border-y border-zinc-200 bg-white">
      <div className="mx-auto max-w-6xl px-6 py-20">
        <div className="mx-auto max-w-2xl text-center">
          <p className="text-sm font-medium uppercase tracking-widest text-zinc-400">
            The problem
          </p>
          <h2 className="mt-3 text-3xl font-semibold tracking-tight">
            You&apos;re flying blind — or drowning in data.
          </h2>
        </div>
        <div className="mt-12 grid gap-6 md:grid-cols-3">
          {[
            {
              title: "Silent money burn",
              body: "A runaway loop or a bloated prompt can burn hundreds of dollars before anyone notices. The invoice arrives; the explanation doesn't.",
            },
            {
              title: "Failures nobody sees",
              body: "Agents fail softly: a tool times out, the agent retries, the user gets a mediocre answer. No alert, no stack trace, no lesson learned.",
            },
            {
              title: "Dashboards, not answers",
              body: "Existing tools show you every span ever recorded. Nobody has time to read 10,000 traces to figure out what to change on Monday.",
            },
          ].map((c) => (
            <div
              key={c.title}
              className="rounded-2xl border border-zinc-200 bg-zinc-50 p-6"
            >
              <h3 className="text-base font-semibold">{c.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-zinc-600">{c.body}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

export function HowItWorks() {
  const steps = [
    {
      n: "1",
      title: "Describe what to observe",
      body: "Write one prompt: what you want to watch — costs, latency, tool calls, errors. Paste it into your coding agent.",
    },
    {
      n: "2",
      title: "Your agent instruments it",
      body: "Your coding agent generates the complete instrumentation with our open-source SDK. Standard OpenTelemetry — nothing proprietary to learn.",
    },
    {
      n: "3",
      title: "Get insights, not traces",
      body: "Agentropy predicts next month's cost, flags the tool that keeps failing, and proposes the exact fix. You approve; it gets better.",
    },
  ];
  return (
    <section id="how" className="mx-auto max-w-6xl px-6 py-20">
      <div className="mx-auto max-w-2xl text-center">
        <p className="text-sm font-medium uppercase tracking-widest text-zinc-400">
          How it works
        </p>
        <h2 className="mt-3 text-3xl font-semibold tracking-tight">
          Observability in one shot.
        </h2>
      </div>
      <div className="mt-12 grid gap-6 md:grid-cols-3">
        {steps.map((s) => (
          <div
            key={s.n}
            className="rounded-2xl border border-zinc-200 bg-white p-6"
          >
            <span className="flex h-10 w-10 items-center justify-center rounded-full bg-zinc-900 text-sm font-semibold text-white">
              {s.n}
            </span>
            <h3 className="mt-4 text-base font-semibold">{s.title}</h3>
            <p className="mt-2 text-sm leading-relaxed text-zinc-600">{s.body}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

export function FeaturesGrid() {
  const features = [
    {
      title: "Everything captured",
      body: "Token usage and cost, latency, agent context, tool calls, errors, full trajectories. If your agent did it, you'll see it.",
    },
    {
      title: "Cost predictions",
      body: "Linear-trend forecasts of daily spend for the next 7 and 30 days — before the invoice surprises you.",
    },
    {
      title: "Failure detection",
      body: "Error-rate spikes, latency regressions, and tools that keep failing — caught by rules, explained in plain English.",
    },
    {
      title: "Concrete proposals",
      body: "Not 'latency is high' but 'parallelize these two tool calls and cap per-step timeouts'. Actions you can ship.",
    },
    {
      title: "Standard OpenTelemetry",
      body: "Capture is 100% standard OTel with GenAI semantic conventions. Our SDK is open source; your data is portable.",
    },
    {
      title: "Beautiful and simple",
      body: "One dashboard that answers three questions: what did it cost, what broke, what do I fix. Nothing else.",
    },
  ];
  return (
    <section id="features" className="border-y border-zinc-200 bg-white">
      <div className="mx-auto max-w-6xl px-6 py-20">
        <div className="mx-auto max-w-2xl text-center">
          <p className="text-sm font-medium uppercase tracking-widest text-zinc-400">
            Features
          </p>
          <h2 className="mt-3 text-3xl font-semibold tracking-tight">
            Simple outside. Smart inside.
          </h2>
        </div>
        <div className="mt-12 grid gap-6 md:grid-cols-3">
          {features.map((f) => (
            <div
              key={f.title}
              className="rounded-2xl border border-zinc-200 bg-zinc-50 p-6"
            >
              <h3 className="text-base font-semibold">{f.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-zinc-600">{f.body}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

export function Comparison() {
  const rows: [string, string, string][] = [
    ["Setup", "One prompt — your coding agent instruments it", "SDK integration, decorators, config"],
    ["Focus", "Insights and predictions first", "Traces and dashboards first"],
    ["Cost forecasting", "Built in (7/30-day projections)", "Not available"],
    ["Improvement proposals", "Concrete, actionable suggestions", "Manual analysis"],
    ["Seats", "Unlimited on every plan", "Per-seat pricing on most plans"],
    ["Starting price", "$19/mo", "$29–$39/mo and up"],
  ];
  return (
    <section id="compare" className="mx-auto max-w-6xl px-6 py-20">
      <div className="mx-auto max-w-2xl text-center">
        <p className="text-sm font-medium uppercase tracking-widest text-zinc-400">
          Why Agentropy
        </p>
        <h2 className="mt-3 text-3xl font-semibold tracking-tight">
          Not another trace viewer.
        </h2>
        <p className="mt-4 text-lg text-zinc-600">
          Langfuse and LangSmith are excellent at showing you what happened.
          Agentropy is built for what happens next.
        </p>
      </div>
      <div className="mx-auto mt-12 max-w-4xl overflow-hidden rounded-2xl border border-zinc-200">
        <table className="w-full bg-white text-left text-sm">
          <thead>
            <tr className="border-b border-zinc-200 bg-zinc-50">
              <th className="px-6 py-4 font-medium text-zinc-500"></th>
              <th className="px-6 py-4 font-semibold">Agentropy</th>
              <th className="px-6 py-4 font-medium text-zinc-500">
                Typical observability tools
              </th>
            </tr>
          </thead>
          <tbody>
            {rows.map(([label, us, them]) => (
              <tr key={label} className="border-b border-zinc-100 last:border-0">
                <td className="px-6 py-4 font-medium text-zinc-500">{label}</td>
                <td className="px-6 py-4 font-medium">{us}</td>
                <td className="px-6 py-4 text-zinc-500">{them}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

export function PricingPreview() {
  return (
    <section className="border-y border-zinc-200 bg-white">
      <div className="mx-auto max-w-6xl px-6 py-20 text-center">
        <p className="text-sm font-medium uppercase tracking-widest text-zinc-400">
          Pricing
        </p>
        <h2 className="mx-auto mt-3 max-w-xl text-3xl font-semibold tracking-tight">
          Indie pricing. Unlimited seats. No surprises.
        </h2>
        <div className="mx-auto mt-10 grid max-w-3xl gap-6 md:grid-cols-2">
          {[
            { name: "Starter", price: "$19", per: "/month" },
            { name: "Pro", price: "$49", per: "/month" },
          ].map((p) => (
            <div
              key={p.name}
              className="rounded-2xl border border-zinc-200 bg-zinc-50 p-8"
            >
              <h3 className="text-base font-semibold">{p.name}</h3>
              <p className="mt-2">
                <span className="text-4xl font-semibold">{p.price}</span>
                <span className="text-zinc-500">{p.per}</span>
              </p>
              <p className="mt-2 text-sm text-zinc-600">
                Unlimited seats · Full insight engine
              </p>
            </div>
          ))}
        </div>
        <Link
          href="/pricing"
          className="mt-8 inline-block rounded-full bg-zinc-900 px-7 py-3 text-sm font-medium text-white hover:bg-zinc-700"
        >
          See full pricing
        </Link>
      </div>
    </section>
  );
}

export function Faq() {
  const items = [
    {
      q: "How is this different from Langfuse or LangSmith?",
      a: "They show you traces; we tell you what to do. Agentropy captures the same standard telemetry, then runs an insight engine over it: cost and latency forecasts, failure detection, and concrete improvement proposals. Plus one-prompt setup, unlimited seats, and lower prices.",
    },
    {
      q: "Do I need to rewrite my agents?",
      a: "No. Describe what you want to observe in one prompt, paste it into your coding agent, and it generates the instrumentation with our open-source SDK. Standard OpenTelemetry underneath — no lock-in.",
    },
    {
      q: "Where does my data live?",
      a: "Your spans are stored in our metrics backend; the capture SDK is open source and speaks standard OTLP, so your instrumentation stays portable. SaaS data (users, workspaces) lives in Supabase.",
    },
    {
      q: "How do the predictions work?",
      a: "The insight engine (built on LangGraph) computes real statistics from your spans — tokens, cost, latency percentiles, error rates — then projects trends and applies detection rules. No black boxes: every insight shows the numbers behind it.",
    },
    {
      q: "Is there a free plan?",
      a: "No free plan at launch — instead, every plan starts with a 14-day full trial. We'd rather be honest about costs than surprise you later.",
    },
  ];
  return (
    <section className="mx-auto max-w-3xl px-6 py-20">
      <div className="text-center">
        <p className="text-sm font-medium uppercase tracking-widest text-zinc-400">
          FAQ
        </p>
        <h2 className="mt-3 text-3xl font-semibold tracking-tight">
          Questions, answered.
        </h2>
      </div>
      <div className="mt-10 space-y-4">
        {items.map((it) => (
          <details
            key={it.q}
            className="rounded-2xl border border-zinc-200 bg-white p-6"
          >
            <summary className="cursor-pointer font-medium">{it.q}</summary>
            <p className="mt-3 text-sm leading-relaxed text-zinc-600">{it.a}</p>
          </details>
        ))}
      </div>
    </section>
  );
}

export function FinalCta() {
  return (
    <section className="mx-auto max-w-6xl px-6 pb-24">
      <div className="rounded-3xl bg-zinc-900 px-6 py-16 text-center text-white">
        <p className="text-sm font-medium uppercase tracking-widest text-zinc-400">
          See it. Improve it.
        </p>
        <h2 className="mx-auto mt-3 max-w-xl text-3xl font-semibold tracking-tight">
          Stop guessing what your agents are doing.
        </h2>
        <div className="mt-8 flex flex-col items-center justify-center gap-4 sm:flex-row">
          <Link
            href="/dashboard"
            className="rounded-full bg-white px-7 py-3 text-sm font-medium text-zinc-900 hover:bg-zinc-200"
          >
            Open the dashboard
          </Link>
          <Link
            href="/docs"
            className="rounded-full border border-zinc-700 px-7 py-3 text-sm font-medium text-white hover:border-zinc-500"
          >
            Read the docs
          </Link>
        </div>
      </div>
    </section>
  );
}

export function LandingFooter() {
  return (
    <footer className="border-t border-zinc-200">
      <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 px-6 py-8 text-sm text-zinc-500 md:flex-row">
        <span className="font-semibold text-zinc-700">Agentropy</span>
        <nav className="flex gap-6">
          <Link href="/pricing" className="hover:text-zinc-900">
            Pricing
          </Link>
          <Link href="/docs" className="hover:text-zinc-900">
            Docs
          </Link>
          <Link href="/login" className="hover:text-zinc-900">
            Log in
          </Link>
          <Link href="/dashboard" className="hover:text-zinc-900">
            Dashboard
          </Link>
        </nav>
        <span>Open-core agent observability. Capture is open source.</span>
      </div>
    </footer>
  );
}
