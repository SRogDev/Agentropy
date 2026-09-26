# @agentropy/sdk

Open-source capture SDK for the Agent Observability platform. Thin wrapper
around the OpenTelemetry Node SDK — standard spans, OTLP/HTTP export.

```ts
import { init, shutdown, genaiAttrs, getTracer } from "@agentropy/sdk";

init({ apiKey: "ao_live_...", serviceName: "my-agent" });

const tracer = getTracer();
tracer.startActiveSpan("agent.run", (span) => {
  span.setAttributes(
    genaiAttrs({
      system: "anthropic",
      requestModel: "claude-opus-4-6",
      inputTokens: 800,
      outputTokens: 150,
    })
  );
  // ... do agent work ...
  span.end();
});

await shutdown(); // flush on exit
```

`genaiAttrs()` follows the OpenTelemetry GenAI semantic conventions
(`gen_ai.*` attributes).
