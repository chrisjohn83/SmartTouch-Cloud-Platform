---
persona: [developer]
task: [observability, remote-access, troubleshooting]
product: [smarttouch-cloud]
difficulty: beginner
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
tags: [logs, loki, grafana, stctl, remote-access, troubleshooting]
related:
  - docs/developers/observability/how-to-instrument-service.md
  - docs/developers/observability/how-to-trace-request.md
  - docs/developers/troubleshooting/why-logs-not-appearing.md
ai-retrieval-questions:
  - "How do I view logs for my service?"
  - "How do I filter logs for a specific session?"
  - "How do I query Loki for Remote Access Service logs?"
  - "How do I stream live logs from stctl?"

owner: developer-experience-team
reviewer: tech-writing-guild
review-cadence: quarterly
---

# How do I view logs for my service?

> **Keyword:** How do I view logs for my service?

SmartTouch aggregates all service logs in Loki. You can access them from the terminal with `stctl logs` or from the Grafana Logs panel. Both methods support filtering by session ID, device ID, log level, and time range.

---

## Goal

View and filter logs from the Remote Access Service, filtered to a specific session.

---

## Prerequisites

- The Remote Access Service deployed and running
- `stctl` authenticated

---

## Method 1 — Stream logs from the terminal

Stream live logs from all pods of your service:

```bash
stctl logs --env dev --service remote-access-service --follow
```

Expected output — structured JSON logs streamed from all pods:

```text
{"level":"info","message":"Session opened","sessionId":"sess-a7c3f1","deviceId":"sensor-001","protocol":"shell","userId":"alex@example.com","timestamp":"2026-06-06T14:05:22Z"}
{"level":"info","message":"Session closed","sessionId":"sess-a7c3f1","duration":135,"closedBy":"user","timestamp":"2026-06-06T14:07:37Z"}
```

Press `Ctrl+C` to stop streaming.

### Filter logs by session ID

```bash
stctl logs --env dev --service remote-access-service \
  --filter sessionId=sess-a7c3f1
```

### Filter logs by device ID

```bash
stctl logs --env dev --service remote-access-service \
  --filter deviceId=sensor-001 \
  --since 1h
```

### Filter by log level

```bash
stctl logs --env dev --service remote-access-service \
  --level error \
  --since 30m
```

### View logs from a specific pod

```bash
stctl pods --env dev --service remote-access-service
# Note the pod name, then:
stctl logs --env dev --service remote-access-service \
  --pod remote-access-service-6c8d4f-ql7rn
```

---

## Method 2 — Query logs in Grafana

Open the pre-built Grafana dashboard for your service:

```bash
stctl dashboard open --name service-logs --env dev
```

### Loki query syntax

The Grafana Logs panel uses LogQL. Common queries for the Remote Access Service:

**All logs from the Remote Access Service:**

```text
{service="remote-access-service", env="dev"}
```

**Error logs only:**

```text
{service="remote-access-service", env="dev"} | json | level="error"
```

**Logs for a specific session:**

```text
{service="remote-access-service", env="dev"} | json | sessionId="sess-a7c3f1"
```

**Logs for a specific device:**

```text
{service="remote-access-service", env="dev"} | json | deviceId="sensor-001"
```

**Session open events in the last hour:**

```text
{service="remote-access-service", env="dev"} | json | message="Session opened"
```

---

## Validation

Logs are accessible when:

```bash
stctl logs --env dev --service remote-access-service --since 5m
# Returns recent log lines from the service
```

---

## Troubleshooting

If no logs appear, see [Why are my logs not appearing?](../troubleshooting/why-logs-not-appearing.md).

---

## Next steps

- [How do I trace a request end-to-end?](./how-to-trace-request.md)
- [Why are my logs not appearing?](../troubleshooting/why-logs-not-appearing.md)
