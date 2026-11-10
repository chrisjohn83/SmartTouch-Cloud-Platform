---
persona: [developer]
task: [onboarding, concepts]
product: [smarttouch-cloud]
difficulty: beginner
status: published
version: "2.0"
platform-version: "2.x"
tags: [api-reference, api-playground, versioning, sandbox]
---

# Platform concepts

## API Reference and API Playground

The **API Reference** is read-only documentation. Use it to inspect endpoints, parameters, schemas, and responses.

The **API Playground** is interactive. Use it to authorize and send requests to a configured server.

## V1 and V2

- V1 documents the original contracts and uses placeholder platform addresses.
- V2 provides runnable Device, Deployment, and Audit Log endpoints through the local FastAPI service.

Choose V2 when you want to test requests locally.

## Local architecture

```text
Browser
  └─ MkDocs portal: http://127.0.0.1:8001
       └─ API Playground
            └─ FastAPI sandbox: http://127.0.0.1:8090
```

## Authentication

All V2 business endpoints require an HTTP bearer token. The local sandbox accepts `demo-token`. The Playground adds the `Bearer` prefix after you authorize.

## Data lifecycle

The local V2 service uses an in-memory store with seeded examples. Restarting the API restores the original devices, deployment, and audit events.
