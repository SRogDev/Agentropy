# agentropy (Python SDK)

Open-source capture SDK for the Agent Observability platform. Thin wrapper
around the OpenTelemetry Python SDK — standard spans, OTLP/HTTP export.

```python
import agentropy
from opentelemetry import trace

agentropy.init(api_key="ao_live_...", service_name="my-agent")

tracer = trace.get_tracer(__name__)
with tracer.start_as_current_span("agent.run") as span:
    for k, v in agentropy.genai_attrs(
        system="openai", request_model="gpt-4o",
        input_tokens=1200, output_tokens=300,
    ).items():
        span.set_attribute(k, v)

agentropy.shutdown()  # flush on exit
```

`genai_attrs()` follows the OpenTelemetry GenAI semantic conventions
(`gen_ai.*` attributes).
