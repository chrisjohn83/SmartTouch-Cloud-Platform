---
persona: [developer]
task: [observability, troubleshooting, logging]
product: [smarttouch-cloud]
difficulty: intermediate
status: published
version: "1.0"
platform-version: "1.x"
last-reviewed: "2026-06-08"
locale: en-US
translation-status: source
translated-from: ""
accessibility:
  reviewed: false
  images-have-alt-text: true
  color-independent: true
  has-text-diagrams: true
tags: [logs, observability, troubleshooting, loki, opentelemetry, remote-access, stctl]
related:
  - docs/developers/observability/how-to-view-logs.md
  - docs/developers/observability/how-to-instrument-service.md
  - docs/developers/api-reference/stctl-cli-reference.md
ai-retrieval-questions:
  - "Why are my logs not appearing?"
  - "Why can I not see logs in Grafana?"
  - "Why is stctl logs returning no results?"
  - "How do I fix missing logs in SmartTouch?"
  - "Why are my remote access session logs missing?"
owner: developer-experience-team
reviewer: tech-writing-guild
review-cadence: quarterly
---

# Why are my logs not appearing?

> **Keyword:** Why are my logs not appearing?

This guide covers the most common reasons logs are missing from `stctl logs` or Grafana, and how to resolve each one.

---

## Quick diagnosis

Run these commands first to narrow down the cause.

```bash
# Verify the service is running and healthy
stctl deploy status remote-access-service --env staging

# Try the simplest possible log query
stctl logs remote-access-service --since 1h --env staging

# Check the OpenTelemetry collector status
stctl status --env staging | grep -i otel
```

If `stctl logs` returns results, the pipeline is working and the issue is a query filter or a Grafana configuration problem. If `stctl logs` returns nothing, the pipeline itself is broken—start from **No logs in stctl logs** below.

---

## No logs in stctl logs

### Symptom

`stctl logs <service_name>` returns no output or the message `No log entries found`.

```text
$ stctl logs remote-access-service --since 1h --env staging
No log entries found for the last 1h.
```

### Diagnosis

Work through these causes in order.

**1. The service isn't emitting structured JSON logs.**

`stctl logs` queries Loki using structured fields. If your service writes plain-text logs, Loki cannot index them and they don't appear.

Check what your service is actually writing:

```bash
stctl exec remote-access-service -- \
  kubectl logs remote-access-service-78d4b-lx9rp --tail=10 --env staging
```

Expected structured output:

```json
{"level":"info","timestamp":"2026-06-08T09:12:00Z","service":"remote-access-service","msg":"session opened","sessionId":"sess-9c4d2e","deviceId":"sensor-001"}
```

If the output is plain text (for example, `INFO session opened`), the OTel SDK is not configured. See [How do I instrument my service?](../observability/how-to-instrument-service.md).

**2. The OTel collector sidecar is not injected.**

The platform injects an OTel collector sidecar into each pod. If the SSD `observability` block is missing or has `logs: false`, the sidecar is absent and logs are not forwarded to Loki.

Check the SSD:

```yaml
observability:
  logs: true
  metrics: true
  traces: true
```

Re-apply if the block is missing or incorrect:

```bash
stctl deploy apply -f smarttouch.yaml --env staging
```

**3. Loki ingestion lag.**

During high load, Loki may have a 2–5 minute ingestion delay. Wait and retry:

```bash
stctl logs remote-access-service --since 10m --env staging
```

**4. Wrong namespace.**

If you deployed to a non-default namespace, pass `--namespace` explicitly:

```bash
stctl logs remote-access-service \
  --env staging \
  --namespace iot-services
```

Or set the default namespace in your `stctl` config:

```bash
export STCTL_NAMESPACE=iot-services
```

### Resolution

The fix depends on the cause identified above:

- Missing OTel SDK → add structured logging — see [How do I instrument my service?](../observability/how-to-instrument-service.md).
- Missing sidecar → add `observability.logs: true` to the SSD and re-apply.
- Namespace mismatch → add `--namespace` flag or set `STCTL_NAMESPACE`.
- Loki lag → wait 5 minutes and retry.

### Prevention

- Add `observability.logs: true` to your SSD template and do not remove it.
- Validate structured log output locally with `docker run` before deploying.
- Add a smoke test in CI that checks for at least one log entry after a test deployment.

---

## Logs visible in stctl but not in Grafana

### Symptoms description

`stctl logs` returns results but the same logs do not appear in Grafana's Explore view or in a Loki panel.

### Resoultion steps

**1. Incorrect Loki data source or label selector.**

In Grafana Explore, verify the data source is set to **Loki** (not Prometheus).

Verify the LogQL query uses the correct label. SmartTouch emits logs under the `service_name` label:

```logql
{service_name="remote-access-service"}
```

Using an incorrect label returns no results without an error message.

**2. Time range is too narrow.**

Grafana's time range defaults to **Last 1 hour**. If you deployed recently, widen the range to **Last 3 hours** or **Last 24 hours**.

**3. Log level filter excludes your entries.**

If a log level filter is active in the Explore panel, entries at other levels are hidden. Remove the filter or set it to **All levels**.

### Resolution steps

Use this baseline LogQL query in Grafana Explore to verify logs are reaching Loki at all:

```logql
{service_name="remote-access-service"} | json
```

If this returns results, narrow the query to your specific use case:

```logql
{service_name="remote-access-service"} | json | sessionId="sess-9c4d2e"
```

If the baseline returns nothing but `stctl logs` does, contact your Platform Engineer — there may be a Loki configuration issue with label mapping.

### Prevention method

- Bookmark the Grafana dashboard for your service and verify it works after each deployment.
- Use the standard label `service_name` in all LogQL queries rather than custom labels that may vary by environment.

---

## Remote access session logs missing

### Symptom of logs not appearing

You opened a remote access session but cannot find session logs. Queries filtered by `sessionId` return no results.

### Diagnosis methods

**1. The service is not emitting `sessionId` in log fields.**

Session logs require the OTel SDK to include `sessionId` and `deviceId` as structured fields. Check the [instrumentation guide](../observability/how-to-instrument-service.md) to confirm these fields are present.

**2. The session was too brief.**

Sessions shorter than 30 seconds may not produce log entries if the OTel batch export interval has not elapsed. The default export interval is 5 seconds — very short sessions may be missed.

**3. You are querying the wrong service.**

Session logs are emitted by the Remote Access Service, not by your application service. Verify you are querying the correct service name:

```bash
stctl logs remote-access-service \
  --filter sessionId=sess-9c4d2e \
  --since 1h \
  --env staging
```

### Resolutions

Search for the session by ID in the Remote Access Service logs:

```bash
stctl logs remote-access-service \
  --filter sessionId=sess-9c4d2e \
  --since 2h \
  --env staging
```

If nothing is found, use the trace ID from the session to correlate across services:

```bash
stctl trace list remote-access-service \
  --session sess-9c4d2e \
  --env staging
```

Then open the trace to see the full request lifecycle:

```bash
stctl trace open <trace_id>
```

### Prevention methods

- Always log `sessionId` and `deviceId` as structured fields in the Remote Access Service.
- Set the OTel batch export interval to `1s` for session-intensive workloads to reduce the risk of missing short-session logs.

---

## Logs appearing but truncated

### Symptoms of log files missing

Log entries appear in `stctl logs` or Grafana but are cut off mid-message.

### Diagnosis steps

Loki has a default maximum log line size of 256 KB. Log lines that exceed this limit are truncated.

This commonly occurs when a log entry includes a full request/response body, a stack trace, or a binary payload.

### Resolution types

Reduce log entry size by:

- Logging request and response bodies at `debug` level only, not `info`.
- Truncating stack traces to the first 10 frames.
- Using a `trace_id` reference in the log entry and storing full payloads in a trace span instead.

### Prevention methods for log not appearing

- Enforce a maximum log message length in your logging library (for example, 4096 characters for the `msg` field).
- Route large diagnostic payloads to distributed traces rather than structured logs.

---

## Related

- [How do I view logs for my service?](../observability/how-to-view-logs.md)
- [How do I instrument my service?](../observability/how-to-instrument-service.md)
- [How do I trace a request end-to-end?](../observability/how-to-trace-request.md)
- [stctl CLI reference](../api-reference/stctl-cli-reference.md)
