---
persona: [developer]
task: [observability, remote-access, tracing]
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
tags: [tracing, jaeger, opentelemetry, distributed-tracing, remote-access, grafana]
related:
  - docs/developers/observability/how-to-instrument-service.md
  - docs/developers/observability/how-to-view-logs.md
ai-retrieval-questions:
  - "How do I trace a request end-to-end on SmartTouch?"
  - "How do I find a distributed trace for a remote access session?"
  - "How do I view traces in Grafana for SmartTouch?"
  - "How do I use a trace ID to find logs?"

owner: developer-experience-team
reviewer: tech-writing-guild
review-cadence: quarterly
---

# How do I trace a request end-to-end?

> **Keyword:** How do I trace a request end-to-end on SmartTouch?

Every remote access session creates a distributed trace that spans the full lifecycle: session open request → authentication → broker connection → agent handshake → session tunnel established. The trace ID links every span across every service so you can follow a single session from the API call to the device.

---

## Goal

Find the distributed trace for a specific remote access session and identify where in the request path a latency or error occurred.

---

## Prerequisites

- `observability.tracing: true` in the Remote Access Service SSD
- The service instrumented with OTel — see [How do I instrument my service?](./how-to-instrument-service.md)
- A recent session ID (from `stctl remote-access list` or the audit log)

---

## How tracing works for remote access sessions

```text
stctl remote-access open (user request)
        │ trace-id: abc123
        ↓
Remote Access Service: authenticate user
        │ span: auth.verify-role
        ↓
Remote Access Service: check device availability
        │ span: device.status-check
        ↓
Remote Access Service: establish broker connection
        │ span: broker.connect
        ↓
Remote Access Agent: accept session request
        │ span: agent.session-accept
        ↓
Session tunnel active
```

Each span is emitted to Jaeger via the OTel Collector and is viewable in Grafana.

---

## Steps

### Step 1 — Find the trace ID for a session

The trace ID is attached to every log line for a session. Retrieve it from the logs:

```bash
stctl logs --env dev --service remote-access-service \
  --filter sessionId=sess-a7c3f1 \
  --since 2h
```

Look for a line containing `traceId`:

```text
{"level":"info","message":"Session opened","sessionId":"sess-a7c3f1","traceId":"abc123def456","deviceId":"sensor-001"}
```

The trace ID is `abc123def456`.

### Step 2 — Open the trace in Grafana

```bash
stctl trace open --trace-id abc123def456 --env dev
```

This opens the Grafana trace view directly at that trace ID. You do not need to search manually.

### Step 3 — Read the trace waterfall

The trace waterfall shows every span in the session lifecycle with its duration. Look for:

- **Long spans** — indicate where latency occurred
- **Error spans** — shown in red; expand to see the error message and stack trace
- **Missing spans** — if the trace ends before `agent.session-accept`, the agent did not receive the session request

Example healthy trace (total: 142ms):

```text
remote-access-service (142ms total)
  ├── auth.verify-role               8ms   ✔
  ├── device.status-check           12ms   ✔
  ├── broker.connect                18ms   ✔
  ├── agent.session-accept         104ms   ✔  ← Most latency here (normal: agent handshake)
  └── session.tunnel-established     0ms   ✔
```

### Step 4 — Correlate traces with logs

In Grafana, click any span in the trace waterfall. A side panel opens showing the logs for that span, filtered by `traceId` automatically. This connects the trace context to the raw log output for the same operation.

### Step 5 — Find all traces for a device

To see all sessions for a specific device:

```bash
stctl trace list \
  --env dev \
  --filter deviceId=sensor-001 \
  --since 24h
```

Expected output:

```text
TRACE ID         SESSION ID     DEVICE        DURATION   STATUS
abc123def456     sess-a7c3f1    sensor-001    142ms      success
def789abc012     sess-b8d4e2    sensor-001    89ms       success
ghi345jkl678     sess-c9e5f3    sensor-001    3200ms     error
```

The `3200ms error` trace is worth investigating — open it with `stctl trace open --trace-id ghi345jkl678`.

---

## Validation

Tracing is working when:

```bash
stctl trace list --env dev --service remote-access-service --since 1h
# Returns trace records for recent sessions
```

---

## Troubleshooting

**`stctl trace list` returns no results**

Tracing may not be enabled. Confirm `observability.tracing: true` in your SSD and that the OTel Collector sidecar is running (`READY: 2/2` in pod status). See [How do I instrument my service?](./how-to-instrument-service.md).

### Trace shows only one span (no downstream spans)

Context propagation is not configured. The OTel SDK must propagate the `traceparent` header in all outbound HTTP and gRPC calls. Check that `getNodeAutoInstrumentations()` (Node.js) or `opentelemetry-instrumentation` (Python) is initialised before other imports.

---

## Next steps

- [How do I view logs for my service?](./how-to-view-logs.md)
- [Why are my logs not appearing?](../troubleshooting/why-logs-not-appearing.md)
