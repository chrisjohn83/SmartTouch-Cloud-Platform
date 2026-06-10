---
persona: [developer]
task: [authentication, getting-started]
product: [smarttouch-cloud]
difficulty: beginner
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
  has-text-diagrams: false
tags: [authentication, bearer-token, stctl, onboarding, sso, credentials]
related:
  - docs/developers/onboarding/prerequisites.md
  - docs/developers/onboarding/first-api-call.md
  - docs/developers/api-reference/stctl-cli-reference.md
ai-retrieval-questions:
  - "How do I authenticate with SmartTouch?"
  - "How do I get a bearer token for the SmartTouch API?"
  - "How do I log in to SmartTouch with stctl?"
  - "How do I use a service account token with SmartTouch?"
  - "How long does a SmartTouch bearer token last?"

owner: developer-experience-team
reviewer: tech-writing-guild
review-cadence: quarterly
---

# Authentication

> **Keyword:** How do I authenticate with SmartTouch?

## Goal

Authenticate with the SmartTouch platform and obtain a bearer token you can use for REST API calls and `stctl` commands.

---

## Prerequisites

- `stctl` installed — see [Prerequisites](./prerequisites.md)
- A SmartTouch platform account with the `developer` role
- SSO credentials provided by your Administrator

---

## Step 1—Log in with stctl

Run the login command. This opens a browser window for SSO authentication.

```bash
stctl auth login
```

Expected output:

```text
Opening browser for SSO login...
Waiting for authentication...
```

Your browser opens the SmartTouch SSO login page. Enter your credentials and complete any MFA prompts.

After you authenticate, the browser displays a confirmation message and `stctl` stores your credentials in `~/.stctl/credentials`.

```text
Authentication successful.
Logged in as: alice@example.com
Context:       production
Token expires: in 8h 00m
```

You do not need to log in again until the token expires (8 hours) or you run `stctl auth logout`.

---

## Step 2—Verify your authentication status

Confirm the login succeeded and check your assigned role.

```bash
stctl auth status
```

Expected output:

```text
Context:    production
User:       alice@example.com
Token:      valid (expires in 7h 58m)
Role:       developer
Namespace:  default
```

If your role shows `developer` or higher, you are ready to proceed. If the role is missing or lower than `developer`, contact your Administrator.

---

## Step 3—Generate a bearer token for REST API calls

All REST API calls require the token in an `Authorization: Bearer` header. Print the current token:

```bash
stctl auth token
```

Expected output (a long JWT string):

```text
eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
```

Store it in a shell variable so you can reuse it across `curl` commands:

```bash
TOKEN=$(stctl auth token)
```

Verify it is set:

```bash
echo $TOKEN
```

---

## Step 4—Make a test API call

Confirm your token works by calling the platform status endpoint:

```bash
curl -s \
  -H "Authorization: Bearer $TOKEN" \
  "https://api.smarttouch.local/v1/devices" \
  | head -c 200
```

Expected output (partial):

```json
{"status":200,"data":[
```

If you see `{"error":"unauthorized"`, the token is expired or the variable was not set. Re-run `stctl auth token` and re-export.

---

## Token expiry and refresh

Bearer tokens expire after 8 hours. `stctl` refreshes them automatically when you run CLI commands. For REST API scripts, you must refresh manually.

**Refresh before a token expires:**

```bash
TOKEN=$(stctl auth token)
```

**Check time remaining:**

```bash
stctl auth status
```

**What happens when a token expires:**

```json
{
  "error": "unauthorized",
  "message": "Bearer token is missing or has expired.",
  "status": 401
}
```

When you receive a `401` response, log in again and re-export the token.

---

## Service account tokens

For non-interactive use (CI pipelines, backend services, cron jobs), use a **service account token** instead of a personal SSO token. Service account tokens are long-lived and do not require browser authentication.

Service account tokens are issued by an Administrator. To request one:

1. Ask your Administrator to create a service account in the SmartTouch Console.
2. The Administrator generates a token and shares it securely (for example, via Vault).
3. Store the token in a secret — never in a `.env` file or source code.

Use a service account token identically to a personal token:

```bash
export TOKEN=<service-account-token>

curl -s \
  -H "Authorization: Bearer $TOKEN" \
  "https://api.smarttouch.local/v1/devices"
```

---

## Using environment variables

You can set the token as an environment variable so `stctl` picks it up automatically, bypassing the stored credentials file:

```bash
export STCTL_TOKEN=$(stctl auth token)
```

This is useful in CI environments where SSO login is not available and a service account token is provided via a secret manager.

---

## Multiple contexts

If you have access to more than one SmartTouch environment (for example, `dev` and `production`), each has its own context in `~/.stctl/config.yaml`.

Switch contexts:

```bash
stctl auth login --context dev
```

Check the current context:

```bash
stctl auth status
```

You can have separate tokens for separate contexts. `stctl` tracks them independently.

---

## Troubleshooting authentication

| Error | Cause | Fix |
| --- | --- | --- |
| `Authentication failed: SSO error` | Incorrect password or MFA failed | Retry login. Confirm SSO credentials with your Administrator. |
| `Token valid but role is missing` | Account exists but no role was assigned | Ask your Administrator to assign the `developer` role. |
| `401 unauthorized` on API call | Token expired or `$TOKEN` variable is empty | Run `TOKEN=$(stctl auth token)` and retry. |
| `stctl: command not found` | `stctl` is not on your PATH | See [Prerequisites](./prerequisites.md). |

---

## Next step

[First API call →](./first-api-call.md)
