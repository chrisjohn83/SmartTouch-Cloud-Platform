---
persona: [developer]
task: [deployment, remote-access]
product: [smarttouch-cloud]
difficulty: beginner
status: published
version: "1.0"
platform-version: "1.x"
last-reviewed: "2026-06-06"
tags: [docker, container, image, harbor, remote-access, websocket, deployment]
sequence: 2
part-of: deploy-first-iot-service
related:
  - docs/developers/get-started/deploy-first-iot-service/01-create-service-spec.md
  - docs/developers/get-started/deploy-first-iot-service/03-verify-deployment.md

ai-retrieval-questions:
  - "How do I build the Remote Access Service image?"
  - "What Dockerfile do I use for the Remote Access Service?"
  - "How do I push the remote access broker image to SmartTouch?"
  - "What ports does the Remote Access Service expose?"

owner: developer-experience-team
reviewer: tech-writing-guild
review-cadence: quarterly
---

# Build and push the Remote Access Service image

> **Keyword:** How do I build the Remote Access Service image?
> **Part of:** [Deploy the Remote Access Service](./index.md) — Step 2 of 3

The Remote Access Service handles persistent WebSocket connections from devices and users simultaneously. Its Dockerfile must expose the session broker port and pass SmartTouch's non-root security requirement.

---

## Goal

Build and push a Remote Access Service container image that passes Harbor's vulnerability scan.

---

## Prerequisites

- Completed [Create the Remote Access Service SSD](./01-create-service-spec.md)
- Docker installed and running
- `stctl` authenticated

---

## Steps

### Step 1 — Authenticate with Harbor

```bash
stctl registry login
```

Expected output:

```text
✔  Logged in to harbor.smarttouch.io
```

### Step 2 — Write the Dockerfile

The Remote Access Service needs to handle long-lived WebSocket connections, so the base image must support the Node.js (or your language's) async I/O model without a hard connection limit. It exposes two ports: `8080` for the session broker WebSocket and REST API, and `8081` for the Prometheus metrics endpoint.

```dockerfile
# Dockerfile — Remote Access Service
FROM node:20-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY src/ ./src/

FROM node:20-alpine AS runtime

# Non-root user required by SmartTouch security policy
RUN addgroup -S rasgroup && adduser -S rasuser -G rasgroup
USER rasuser

WORKDIR /app
COPY --from=builder /app .

# 8080 — WebSocket session broker + REST API
# 8081 — Prometheus metrics
EXPOSE 8080 8081

# Health check verifies the session broker is accepting connections,
# not just that the process is alive
HEALTHCHECK --interval=15s --timeout=5s --start-period=15s \
  CMD wget -qO- http://localhost:8080/health || exit 1

CMD ["node", "src/index.js"]
```

### Step 3 — Build the image

```bash
docker build \
  --tag harbor.smarttouch.io/myteam/remote-access-service:1.0.0 \
  --platform linux/amd64 \
  .
```

### Step 4 — Run a local smoke test

```bash
docker run --rm -p 8080:8080 -p 8081:8081 \
  harbor.smarttouch.io/myteam/remote-access-service:1.0.0
```

In a second terminal, verify both endpoints:

```bash
curl http://localhost:8080/health
```

Expected:

```text
{"status":"ok","broker":"ready","sessions":{"active":0,"limit":50}}
```

```bash
curl http://localhost:8081/metrics | grep remote_access
```

Expected — metric names beginning with `remote_access_`:

```text
# HELP remote_access_sessions_active Currently active remote access sessions
remote_access_sessions_active 0
# HELP remote_access_sessions_total Total sessions opened since startup
remote_access_sessions_total 0
```

Press `Ctrl+C` to stop.

### Step 5 — Push to Harbor

```bash
docker push harbor.smarttouch.io/myteam/remote-access-service:1.0.0
```

### Step 6 — Confirm the vulnerability scan passed

```bash
stctl registry scan-status \
  --image harbor.smarttouch.io/myteam/remote-access-service:1.0.0
```

Expected output:

```text
Scan status:   completed
Critical CVEs: 0
High CVEs:     0
Policy:        PASS
```

Images with Critical or High CVEs are blocked from `staging` and `prod` deployments. Update the base image or dependencies and rebuild if any are found.

---

## Validation

```bash
stctl registry list --service remote-access-service
# Image appears with a recent PUSHED timestamp

stctl registry scan-status --image harbor.smarttouch.io/myteam/remote-access-service:1.0.0
# Policy: PASS
```

---

## Troubleshooting

**Health check returns `"broker":"starting"`**
The session broker is still initialising. Increase `start-period` in the `HEALTHCHECK` instruction to 30 seconds if your service needs more time to load TLS certificates on startup.

**`exec format error`** on deploy
Rebuild with `--platform linux/amd64` — the image was built for the wrong CPU architecture.

**Harbor scan shows High CVEs**
Update the Node.js base image to the latest `node:20-alpine` patch and rebuild. If CVEs are in application dependencies, run `npm audit fix` first.

---

## Next steps

→ Continue to **Step 3:** [Verify the session broker is running](./03-verify-deployment.md)
