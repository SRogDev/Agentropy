"""agentropy — open-source capture SDK for the Agent Observability platform.

Thin wrapper around the OpenTelemetry Python SDK. We do NOT reinvent
instrumentation: spans are standard OTel spans, exported via OTLP/HTTP to the
platform's API.
"""

from .sdk import genai_attrs, init, shutdown

__all__ = ["init", "shutdown", "genai_attrs"]
__version__ = "0.1.0"
