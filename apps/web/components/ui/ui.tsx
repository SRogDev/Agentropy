import type { ReactNode } from "react";

export function Card({
  title,
  hint,
  children,
}: {
  title: string;
  hint?: ReactNode;
  children: ReactNode;
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

export function Container({ children }: { children: ReactNode }) {
  return <div className="mx-auto max-w-6xl px-6">{children}</div>;
}

export function SectionHeading({
  eyebrow,
  title,
  body,
}: {
  eyebrow?: string;
  title: string;
  body?: string;
}) {
  return (
    <div className="mx-auto max-w-2xl text-center">
      {eyebrow && (
        <p className="text-sm font-medium uppercase tracking-widest text-zinc-400">
          {eyebrow}
        </p>
      )}
      <h2 className="mt-3 text-3xl font-semibold tracking-tight">{title}</h2>
      {body && <p className="mt-4 text-lg text-zinc-600">{body}</p>}
    </div>
  );
}
