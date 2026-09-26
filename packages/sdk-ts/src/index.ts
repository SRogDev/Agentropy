/**
 * @agentropy/sdk — open-source capture SDK for the Agent Observability platform.
 *
 * Thin wrapper around the OpenTelemetry Node SDK. We do NOT reinvent
 * instrumentation: spans are standard OTel spans, exported via OTLP/HTTP
 * to the platform's API.
 */
import { trace, type Attributes, type Tracer } from "@opentelemetry/api";
import { OTLPTraceExporter } from "@opentelemetry/exporter-trace-otlp-http";
import { resourceFromAttributes } from "@opentelemetry/resources";
import { ATTR_SERVICE_NAME } from "@opentelemetry/semantic-conventions";
import { NodeSDK } from "@opentelemetry/sdk-node";

export interface InitOptions {
  apiKey: string;
  /** Base URL of the API, e.g. "http://localhost:8000". */
  endpoint?: string;
  serviceName?: string;
}

let sdk: NodeSDK | undefined;

/**
 * Configure OpenTelemetry to send spans to the API. Call once at startup.
 *
 *   import { init } from "@agentropy/sdk";
 *   init({ apiKey: "ao_live_...", serviceName: "my-agent" });
 */
export function init({
  apiKey,
  endpoint = "http://localhost:8000",
  serviceName = "agent-app",
}: InitOptions): void {
  if (sdk) return;
  const exporter = new OTLPTraceExporter({
    url: `${endpoint.replace(/\/$/, "")}/v1/traces`,
    headers: { "X-API-Key": apiKey },
  });
  sdk = new NodeSDK({
    resource: resourceFromAttributes({ [ATTR_SERVICE_NAME]: serviceName }),
    traceExporter: exporter,
  });
  sdk.start();
}

/** Flush pending spans and shut down. Call on process exit. */
export async function shutdown(): Promise<void> {
  await sdk?.shutdown();
  sdk = undefined;
}

export interface GenAiAttrsOptions {
  system?: string;
  requestModel?: string;
  inputTokens?: number;
  outputTokens?: number;
  responseId?: string;
  operationName?: string;
}

/**
 * Build span attributes following the OpenTelemetry GenAI semantic
 * conventions (gen_ai.*).
 */
export function genaiAttrs(o: GenAiAttrsOptions): Attributes {
  const attrs: Attributes = {};
  if (o.system !== undefined) attrs["gen_ai.system"] = o.system;
  if (o.requestModel !== undefined)
    attrs["gen_ai.request.model"] = o.requestModel;
  if (o.inputTokens !== undefined)
    attrs["gen_ai.usage.input_tokens"] = o.inputTokens;
  if (o.outputTokens !== undefined)
    attrs["gen_ai.usage.output_tokens"] = o.outputTokens;
  if (o.responseId !== undefined) attrs["gen_ai.response.id"] = o.responseId;
  if (o.operationName !== undefined)
    attrs["gen_ai.operation.name"] = o.operationName;
  return attrs;
}

export function getTracer(name = "agentropy"): Tracer {
  return trace.getTracer(name);
}
