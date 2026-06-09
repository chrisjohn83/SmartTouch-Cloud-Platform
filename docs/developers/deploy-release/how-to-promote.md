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
tags: [promotion, staging, production, release, gitops, remote-access]
related:
  - docs/developers/deploy-release/how-to-deploy-service.md
  - docs/developers/deploy-release/how-to-canary-deployment.md
ai-retrieval-questions:
  - "How do I promote a release to production?"
  - "How do I deploy to staging on SmartTouch?"
  - "How do I release the Remote Access Service to prod?"
  - "What is the production promotion process on SmartTouch?"
owner: developer-experience-team
reviewer: tech-writing-guild
review-cadence: quarterly
---

# How do I promote a release to production?

> **Keyword:** How do I promote a release to production?

Promotion in SmartTouch is a pull request workflow. A merge to `main` deploys to `staging` automatically. A release tag opens a pull request against the `prod` overlay, which requires a Platform Engineer or Administrator to approve.

---

## Goal

Promote the Remote Access Service from `staging` to `prod`.

---

## Prerequisites

- The service is deployed and healthy in `staging`
- Smoke tests against `staging` have passed
- You have a GitHub account with write access to the repository

---

## Promotion path

```text
dev    ← automatic on every PR merge to main
  ↓
staging  ← automatic on every merge to main (after dev is healthy)
  ↓
prod     ← requires a tagged release + manual PR approval
```

---

## Steps

### Step 1 — Verify staging is healthy

Before creating a release, confirm the service is running correctly in `staging`:

```bash
stctl status --env staging --service remote-access-service
```

Expected:

```text
Status:    Running
Replicas:  2/2 ready
Image:     harbor.smarttouch.io/myteam/remote-access-service:1.1.0
```

Run a full probe against staging:

```bash
stctl remote-access probe --env staging
```

Expected:

```text
✔  Probe session opened and closed successfully
Broker latency: 22ms
```

### Step 2 — Create a release tag

Tag the commit on `main` that you want to release:

```bash
git checkout main
git pull
git tag v1.1.0 -m "Release Remote Access Service v1.1.0"
git push origin v1.1.0
```

### Step 3 — GitHub Actions creates the prod promotion PR

When the tag is pushed, GitHub Actions automatically:

1. Verifies the image for `1.1.0` exists in Harbor
2. Runs the Harbor vulnerability scan
3. Updates the image tag in `k8s/overlays/prod/`
4. Opens a pull request titled: `chore: promote remote-access-service v1.1.0 to prod`

The pull request includes a deployment summary showing what changed between the current prod version and the new version.

### Step 4 — Platform Engineer or Administrator approves the PR

The prod promotion PR requires approval from a `platform-engineer` or `administrator` role. The approver verifies:

- The image tag matches the release tag
- The vulnerability scan passed
- The staging deployment is healthy

### Step 5 — Merge the pull request

After approval, merge the pull request. Argo CD detects the manifest change and deploys to `prod`.

Monitor the prod deployment:

```bash
stctl status --env prod --service remote-access-service
```

### Step 6 — Verify prod deployment

```bash
stctl remote-access probe --env prod
```

Expected:

```text
✔  Probe session opened and closed successfully
Environment: prod
Broker latency: 19ms
```

---

## Validation

Promotion is complete when:

| Check | Command | Expected |
|---|---|---|
| Correct version running | `stctl status --env prod --service remote-access-service` | Image tag matches release tag |
| Broker active | `stctl remote-access probe --env prod` | Probe succeeds |

---

## Troubleshooting

**GitHub Actions did not create a prod PR after the tag push**

Check the Actions workflow run in GitHub. Common causes: the image for the tag does not exist in Harbor, or the vulnerability scan failed. Rebuild and push the image, then re-push the tag.

**Approver cannot find the pull request**

The PR is opened against the `prod` branch in the same repository. Check the Pull Requests tab filtered by `base: prod`.

---

## Next steps

- [How do I run a canary deployment?](./how-to-canary-deployment.md)
- [How do I roll back a deployment?](./how-to-rollback.md)
