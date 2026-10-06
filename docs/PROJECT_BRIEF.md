# Agentropy — Project Brief

> Full project context in one file. Hand this to ANOTHER AI (GPT, etc.) for planning
> and ideation, then bring the refined specs back. Keep this file accurate — it is the handoff doc.
> For the current timeline see `STATUS.md`. For how to work in this repo see `AGENTS.md`.

## One-liner
Agentropy ('See it. Improve it.') is Roger's agent observability platform — English-first, open-core, indie-priced.

## Problem & audience
Agent observability tools are complex and expensive; indie builders need something simpler, beautiful, and fairly priced.

## Product (what it is / is not)
Agent observability: OTel-standard capture (open source) + proprietary insight engine (verified predictions/warnings/proposals via LangGraph). Simpler than competitors, beautiful UI, unlimited seats. NOT an all-in-one LLM platform — observability only.

## Key decisions (locked)
- Open-core: OTel-standard capture open source, insight engine proprietary.
- Indie pricing (~$19/$49 subscription), free trial only.
- English-first product.
- Insight LLM polish via OpenRouter (openai/gpt-4o-mini).

## Stack
Next.js web, FastAPI api, Python + TS SDKs (turbo/pnpm monorepo), Supabase, Polar, LangGraph, OpenRouter.

## Business model
SaaS subscription ~$19/$49, unlimited seats, free trial only. Polar billing.

## Open questions
- Keys blocked on Roger (Supabase, Polar, OpenRouter).
- Which insights prove valuable on real data — needs live testing.
