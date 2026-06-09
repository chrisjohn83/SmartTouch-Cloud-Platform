---
persona: [developer]
task: [remote-access, api-reference, device-management]
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
tags: [api, rest, remote-access, devices, sessions, audit-log, reference]
related:
  - docs/developers/api-reference/stctl-cli-reference.md
  - docs/developers/observability/how-to-trace-request.md
  - docs/developers/troubleshooting/why-device-not-connecting.md
ai-retrieval-questions:
  - "What REST API endpoints does SmartTouch provide?"
  - "How do I open a remote access session via the API?"
  - "How do I list devices using the SmartTouch API?"
  - "What is the SmartTouch REST API base URL?"
  - "How do I authenticate with the SmartTouch REST API?"
owner: developer-experience-team
reviewer: tech-writing-guild
review-cadence: quarterly
---

# SmartTouch REST API reference

> **Keyword:** What REST API endpoints does SmartTouch provide?

The SmartTouch REST API gives you programmatic access to devices, remote access sessions, and audit logs. Use it to automate session management, integrate with external tooling, or build custom dashboards.

All API calls require authentication. The `stctl` CLI wraps the majority of these endpoints—use the API directly when you need fine-grained control or when calling from a non-interactive context such as a CI pipeline or server-side service.

---

## Base URL

```text
https://api.<your-platform-domain>/v1
```

Replace `<your-platform-domain>` with the host name of your SmartTouch installation. For local development, the default base URL is:

```text
https://api.smarttouch.local/v1
```

---

## Authentication

All requests require a bearer token in the `Authorization` header.

```text
Authorization: Bearer <token>
```

**Obtain a token:**

```bash
stctl auth token
```

Tokens expire after 8 hours. Service accounts use long-lived tokens issued by an Administrator—see [Manage service account tokens](../secrets-config/how-to-manage-secrets.md).

**Error response when token is missing or expired:**

```json
{
  "error": "unauthorized",
  "message": "Bearer token is missing or has expired.",
  "status": 401
}
```

---

## Common response fields

Every response body includes:

| Field | Type | Description |
| --- | --- | --- |
| `status` | integer | HTTP status code |
| `data` | object or array | Response payload |
| `meta` | object | Pagination metadata (list endpoints only) |
| `error` | string | Machine-readable error code (error responses only) |
| `message` | string | Human-readable error description (error responses only) |

---

## Error codes

| HTTP status | Error code | Meaning |
| --- | --- | --- |
| 400 | `bad_request` | Request body or query parameters are invalid |
| 401 | `unauthorized` | Token is missing, invalid, or expired |
| 403 | `forbidden` | Token doesn't have the required permission for this operation |
| 404 | `not_found` | The requested resource doesn't exist |
| 409 | `conflict` | A session is already open for this device with the requested protocol |
| 422 | `unprocessable_entity` | Request is valid but cann't be completed—for example, the device agent is offline |
| 429 | `rate_limited` | Too many requests—back off and retry after the `Retry-After` header value |
| 500 | `internal_error` | Platform error—check the SmartTouch status page |

---

## Rate limits

| Endpoint group | Limit |
| --- | --- |
| `GET /devices` | 120 requests per minute |
| `POST /remote-access/sessions` | 30 requests per minute |
| `GET /audit/remote-access` | 60 requests per minute |

When a rate limit is exceeded, the API returns `429` with a `Retry-After` header indicating when the limit resets.

---

## Related

- [stctl CLI reference](./stctl-cli-reference.md)
- [How do I trace a request end-to-end?](../observability/how-to-trace-request.md)
- [Why is my device not connecting?](../troubleshooting/why-device-not-connecting.md)
