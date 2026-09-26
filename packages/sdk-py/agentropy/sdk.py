"""One-line OpenTelemetry setup pointed at the Agent Observability API."""

from __future__ import annotations

from typing import Any, Dict

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

_configured = False


def init(
    *,
    api_key: str,
    endpoint: str = "http://localhost:8000",
    service_name: str = "agent-app",
) -> None:
    """Configure OpenTelemetry to send spans to the API. Call once at startup.

    Example:
        import agentropy
        agentropy.init(api_key="ao_live_...", service_name="my-agent")
    """
    global _configured
    if _configured:
        return
    exporter = OTLPSpanExporter(
        endpoint=f"{endpoint.rstrip('/')}/v1/traces",
        headers={"X-API-Key": api_key},
    )
    provider = TracerProvider(resource=Resource.create({"service.name": service_name}))
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    _configured = True


def shutdown() -> None:
    """Flush pending spans. Call on process exit."""
    provider = trace.get_tracer_provider()
    shutdown_fn = getattr(provider, "shutdown", None)
    if callable(shutdown_fn):
        shutdown_fn()


def genai_attrs(
    *,
    system: str | None = None,
    request_model: str | None = None,
    input_tokens: int | None = None,
    output_tokens: int | None = None,
    response_id: str | None = None,
    operation_name: str | None = None,
) -> Dict[str, Any]:
    """Build span attributes following the OpenTelemetry GenAI semantic
    conventions (gen_ai.*). Set them on the span you want observed:

        with tracer.start_as_current_span("agent.run") as span:
            for k, v in agentropy.genai_attrs(
                system="openai", request_model="gpt-4o",
                input_tokens=1200, output_tokens=300,
            ).items():
                span.set_attribute(k, v)
    """
    attrs: Dict[str, Any] = {}
    if system is not None:
        attrs["gen_ai.system"] = system
    if request_model is not None:
        attrs["gen_ai.request.model"] = request_model
    if input_tokens is not None:
        attrs["gen_ai.usage.input_tokens"] = input_tokens
    if output_tokens is not None:
        attrs["gen_ai.usage.output_tokens"] = output_tokens
    if response_id is not None:
        attrs["gen_ai.response.id"] = response_id
    if operation_name is not None:
        attrs["gen_ai.operation.name"] = operation_name
    return attrs
