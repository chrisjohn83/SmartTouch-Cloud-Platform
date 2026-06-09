---
persona: [developer]
task: [deployment, remote-access]
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
tags: [rollback, deployment, argo-cd, remote-access, incident]
related:
  - docs/developers/deploy-release/how-to-deploy-service.md
  - docs/developers/troubleshooting/why-deployment-failing.md
ai-retrieval-questions:
  - "How do I roll back a deployment on SmartTouch?"
  - "How do I revert the Remote Access Service to the previous version?"
  - "How do I undo a bad deployment?"
  - "What is the fastest way to roll back on SmartTouch?"
owner: developer-experience-team
reviewer: tech-writing-guild
review-cadence: quarterly
---

# How do I roll back a deployment?

> **Keyword:** How do I roll back a deployment on SmartTouch?

SmartTouch provides two rollback methods. Use `stctl rollback` for the fastest recovery during an incident. Use a git revert pull request for a traceable, 'auditable' rollback.

---

## Goal

Revert the Remote Access Service in `dev` (or `staging`) to the last known good version.

---

## Prerequisites

- `stctl` installed and authenticated
- The service has a previous successful deployment

---

## Method 1—Fast rollback with 'stctl' (recommended during an incident)

This method reverts the cluster state immediately without a pull request. You can use it when an incident is in active status and every minute matters.

### Step 1—Identify the previous deployment

```bash
stctl deployment history --env dev --service remote-access-service
```

Expected output:

```text
REVISION   IMAGE TAG   DEPLOYED BY      DEPLOYED AT           STATUS
5          1.1.0       github-actions   2026-06-06T14:30:00Z  current
4          1.0.1       github-actions   2026-06-05T10:15:00Z  healthy
3          1.0.0       github-actions   2026-06-04T09:00:00Z  healthy
```

Revision 4 (`1.0.1`) is the last healthy deployment to roll back to.

### Step 2—Roll back to the previous revision

```bash
stctl rollback --env dev --service remote-access-service --revision 4
```

Expected output:

```text
✔  Rollback initiated
Service:       remote-access-service
Rolling back:  revision 5 (1.1.0) → revision 4 (1.0.1)
ETA:           ~60 seconds
```

### Step 3—Verify the rollback completed

```bash
stctl status --env dev --service remote-access-service
```

Expected:

```text
Status:   Running
Replicas: 2/2 ready
Image:    harbor.smarttouch.io/myteam/remote-access-service:1.0.1
```

Run a probe to confirm remote access sessions are working again:

```bash
stctl remote-access probe --env dev
```

---

## Method 2—Audit rollback via git revert

This method creates a pull request that reverses the offending commit. Use it for non-urgent rollbacks where a full audit trail is required (for example, production rollbacks or compliance environments).

### Step 1—Find the commit that caused the problem

```bash
git log --oneline -10
```

```text
a3f9c12 feat: update remote-access-service to v1.1.0
b7d2e41 fix: update session timeout configuration
...
```

### Step 2—Revert the commit

```bash
git revert a3f9c12 --no-commit
git commit -m "revert: roll back remote-access-service from v1.1.0 to v1.0.1"
git push origin fix/rollback-v1.1.0
```

### Step 3—Open and merge the revert pull request

Open a pull request from `fix/rollback-v1.1.0` to `main`. The pull request shows exactly what changed. After approval and merge, Argo CD deploys the reverted state automatically.

---

## Validation

Rollback is complete when:

| Check | Command | Expected |
| --- | --- | --- |
| Correct image running | `stctl status --env dev --service remote-access-service` | Previous image tag |
| Session broker active | `stctl remote-access probe --env dev` | Probe succeeds |
| Active sessions unaffected | `stctl remote-access list --env dev` | Sessions that were open before rollback remain open |

> **Note on active sessions:** A rollback performs a rolling update. Sessions open during the rollback may be interrupted if the pod handling the session is replaced. Warn users before initiating a rollback during business hours.

---

## Troubleshooting

**`stctl rollback` fails with `no previous revision found`**

The service has only one deployment revision. You have nothing to roll back to. Deploy a known-good image tag directly:

```bash
stctl deploy --env dev --service remote-access-service \
  --image harbor.smarttouch.io/myteam/remote-access-service:1.0.0
```

---

## Next steps

- [How do I deploy a service?](./how-to-deploy-service.md)
- [Why is my deployment failing?](../troubleshooting/why-deployment-failing.md)
