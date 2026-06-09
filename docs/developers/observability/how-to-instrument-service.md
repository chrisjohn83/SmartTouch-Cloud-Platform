---
persona: [developer]
task: [observability, remote-access]
product: [smarttouch-cloud]
difficulty: intermediate
status: published
version: "1.0"
platform-version: "1.x"
last-reviewed: "2026-06-06"
locale: en-US
translation-status: source
translated-from: ""
accessibility:
  reviewed: false
  images-have-alt-text: true
  color-independent: true
  has-text-diagrams: true
tags: [opentelemetry, instrumentation, metrics, traces, logs, remote-access]
related:
  - docs/developers/observability/how-to-view-logs.md
  - docs/developers/observability/how-to-trace-request.md
ai-retrieval-questions:
  - "How do I instrument my SmartTouch service?"
  - "How do I add OpenTelemetry to the Remote Access Service?"
  - "How do I emit metrics from my service?"
  - "How do I add distributed tracing to a SmartTouch service?"

owner: developer-experience-team
reviewer: tech-writing-guild
review-cadence: quarterly
---

# How do I instrument my service?

> **Keyword:** How do I instrument my SmartTouch service?

SmartTouch uses the OpenTelemetry (OTel) standard for all observability signals — metrics, logs, and traces. You instrument your service once with the OTel SDK; SmartTouch routes the signals to Prometheus, Loki, and Jaeger automatically.

---

## Goal

Add OpenTelemetry instrumentation to the Remote Access Service so that session metrics, structured logs, and distributed traces are visible in Grafana.

---

## Prerequisites

- `observability.metrics: true` and `observability.tracing: true` in your SSD
- Node.js or Python service (examples provided for both)

---

## How SmartTouch observability works

```text
Your service (OTel SDK)
        ↓
OTel Collector (sidecar in your pod)
        ↓
  ├── Metrics → Prometheus → Grafana
  ├── Logs   → Loki       → Grafana
  └── Traces → Jaeger     → Grafana
```

The OTel Collector sidecar is injected automatically when `observability.metrics: true` in the SSD. You do not configure the collector directly.

---

## Steps

### Step 1 — Install the OTel SDK

### Node.js installation

```bash
npm install @opentelemetry/sdk-node \
            @opentelemetry/auto-instrumentations-node \
            @opentelemetry/exporter-otlp-grpc
```

### Python

```bash
pip install opentelemetry-sdk \
            opentelemetry-instrumentation \
            opentelemetry-exporter-otlp-proto-grpc --break-system-packages
```

### Step 2 — Initialise the SDK

Create a file that initialises OTel before your service starts. This file must be loaded before any other imports.

Node.js — `src/telemetry.js`

```javascript
const { NodeSDK } = require('@opentelemetry/sdk-node');
const { getNodeAutoInstrumentations } = require('@opentelemetry/auto-instrumentations-node');
const { OTLPTraceExporter } = require('@opentelemetry/exporter-otlp-grpc');

const sdk = new NodeSDK({
  serviceName: 'remote-access-service',
  traceExporter: new OTLPTraceExporter({
    url: process.env.OTEL_EXPORTER_OTLP_ENDPOINT || 'http://localhost:4317',
  }),
  instrumentations: [getNodeAutoInstrumentations()],
});

sdk.start();
```

Load it as the first line of your entry point:

```javascript
// src/index.js
require('./telemetry');   // Must be first
const app = require('./app');
```

**Python — `telemetry.py`**

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
import os

def init_telemetry(service_name: str):
    provider = TracerProvider()
    exporter = OTLPSpanExporter(
        endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
    )
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
```

### Step 3 — Add custom metrics for remote access sessions

Track session-specific metrics that are relevant to the Remote Access Service:

#### Node.js metrics

```javascript
const { metrics } = require('@opentelemetry/api');

const meter = metrics.getMeter('remote-access-service');

// Counter: total sessions opened
const sessionsOpened = meter.createCounter('remote_access_sessions_opened_total', {
  description: 'Total number of remote access sessions opened',
});

// Gauge: currently active sessions
const activeSessions = meter.createObservableGauge('remote_access_sessions_active', {
  description: 'Number of currently active remote access sessions',
});

// Histogram: session duration in seconds
const sessionDuration = meter.createHistogram('remote_access_session_duration_seconds', {
  description: 'Duration of completed remote access sessions in seconds',
  boundaries: [10, 60, 300, 900, 1800],
});

// Emit metrics when a session opens
function onSessionOpen(sessionId, protocol) {
  sessionsOpened.add(1, { protocol });
}

// Emit metrics when a session closes
function onSessionClose(sessionId, durationSeconds, protocol) {
  sessionDuration.record(durationSeconds, { protocol });
}
```

### Step 4 — Add structured logging

SmartTouch Loki indexes logs by `service`, `env`, and any additional labels you include. Structure your logs as JSON:

#### Node.js logging

```javascript
function log(level, message, fields = {}) {
  console.log(JSON.stringify({
    level,
    message,
    service: 'remote-access-service',
    timestamp: new Date().toISOString(),
    ...fields,
  }));
}

// Usage
log('info', 'Session opened', {
  sessionId: 'sess-a7c3f1',
  deviceId: 'sensor-001',
  protocol: 'shell',
  userId: 'alex@example.com',
});
```

Always include `sessionId` and `deviceId` in session-related log lines. These fields are used to correlate logs with traces in Grafana.

### Step 5 — Verify signals are flowing

After deploying, check that Grafana is receiving data:

```bash
stctl dashboard open --name service-overview --env dev
```

In the Grafana dashboard, confirm:

- The `remote_access_sessions_opened_total` metric is increasing as sessions open
- Log lines from your service appear in the Logs panel
- Traces appear in the Traces panel after opening a session

---

## Validation

Instrumentation is working when:

| Signal | Where to check | Expected |
| --- | --- | --- |
| Metrics | `stctl dashboard open --name service-overview --env dev` | `remote_access_sessions_opened_total` counter visible |
| Logs | Same dashboard, Logs panel | Structured JSON log lines with `service: remote-access-service` |
| Traces | Same dashboard, Traces panel | Trace spans visible after a session is opened |

---

## Troubleshooting

No metrics in Grafana after deployment

Confirm `observability.metrics: true` is in your SSD and the service is running. Then check whether the OTel Collector sidecar is running in your pod:

```bash
stctl pods --env dev --service remote-access-service
```

Each pod should show `READY: 2/2` — the service container and the OTel Collector sidecar.

---

## Next steps

- [How do I view logs for my service?](./how-to-view-logs.md)
- [How do I trace a request end-to-end?](./how-to-trace-request.md)
