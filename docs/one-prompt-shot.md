# Agentropy — One-Prompt-Shot Instrumentation Template

Give this prompt to your coding agent. It describes **what you want to observe**;
your agent generates the complete instrumentation using the Agentropy SDK.
English is the primary language for all prompts, docs, and UI.

---

Copy everything below the line and paste it into your coding agent:

---

I want observability for my AI agents using **Agentropy**.

Setup:

```bash
pip install agentropy
```

```python
import agentropy

agentropy.init(
    api_key="<YOUR_API_KEY>",
    endpoint="https://api.agentropy.dev",
)
```

```typescript
// or, for Node.js:
import { init } from "@agentropy/sdk";

init({ apiKey: "<YOUR_API_KEY>", endpoint: "https://api.agentropy.dev" });
```

Now instrument my codebase so that Agentropy captures **all** of the following:

1. **Token usage and estimated cost** — per LLM call, per agent run, per user/session.
2. **Latency** — per LLM call, per tool call, end-to-end per agent run.
3. **Agent context** — the inputs, retrieved documents, and conversation state
   each agent step sees (summarized, never full PII).
4. **Tool calls** — name, arguments (redacted where sensitive), duration, success/failure.
5. **Errors** — exceptions, retries, and fallbacks with full stack context.
6. **Trajectories** — the complete step-by-step path of every agent run,
   linked as one trace.

Rules for the instrumentation you generate:

- Use the Agentropy SDK's one-line `init()` — do not hand-roll OpenTelemetry setup.
- Tag every span with GenAI semantic-convention attributes
  (`gen_ai.system`, `gen_ai.request.model`, `gen_ai.usage.input_tokens`,
  `gen_ai.usage.output_tokens`, etc.) via the SDK helpers.
- Correlate everything under a single trace per agent run
  (use `trace_id` / `session_id` consistently).
- Never send secrets, API keys, or raw PII in span attributes — redact them.
- Keep the instrumentation code minimal and centralized (one module),
  so it is easy to review and remove.

After instrumenting, verify: run one agent task end-to-end and confirm the
trace appears in the Agentropy dashboard with tokens, cost, latency, tool
calls, and the full trajectory visible.
