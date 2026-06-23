---
persona: [developer]
task: [deployment, remote-access]
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
tags: [deployment, github-actions, argo-cd, ssd, remote-access]
related:
  - docs/developers/deploy-release/how-to-rollback.md
  - docs/developers/deploy-release/how-to-promote.md
  - docs/developers/get-started/deploy-first-iot-service/index.md
ai-retrieval-questions:
  - "How do I deploy a service on SmartTouch?"
  - "How do I deploy the Remote Access Service?"
  - "How do I trigger a deployment with GitHub Actions?"
  - "How does Argo CD deploy my service?"
owner: developer-experience-team
reviewer: tech-writing-guild
review-cadence: quarterly
---

# How do I deploy a service?

> **Keyword:** How do I deploy a service on SmartTouch?

SmartTouch uses a GitOps deployment model. You push code; GitHub Actions builds and tests it; Argo CD detects the manifest change and deploys to the target environment. You don't run `kubectl apply` or access the cluster directly.

---

## Goal

Deploy a new version of the Remote Access Service to the `dev` environment.

---

## Prerequisites

- A valid `smarttouch.yaml` SSD file committed to your repository—see [Create the Remote Access Service SSD](../get-started/deploy-first-iot-service/01-create-service-spec.md)
- Container image built and pushed to Harbor—see [Build and push the Remote Access Service image](../get-started/deploy-first-iot-service/02-build-push-image.md)
- `stctl` installed and authenticated

---

## How the deployment pipeline works

```text
git push (feature branch)
        ↓
GitHub Actions: lint → test → build image → push to Harbor
        ↓
GitHub Actions: update image tag in k8s/overlays/dev/
        ↓
Argo CD: detects manifest change → syncs cluster
        ↓
Service running in dev environment
```

Argo CD polls Git every 3 minutes. A deployment to `dev` typically completes within 5 minutes of a push.

---

## Steps

### Step 1—Update the image tag in your SSD

When you release a new version, update the image tag in `smarttouch.yaml`:

```yaml
deployment:
  image: harbor.smarttouch.io/myteam/remote-access-service:1.1.0
```

Commit and push:

```bash
git add smarttouch.yaml
git commit -m "feat: update remote-access-service to v1.1.0"
git push origin feature/v1.1.0
```

### Step 2—Open a pull request

Open a pull request against `main`. GitHub Actions runs automatically:

```text
✔  Lint passed
✔  Unit tests passed (47/47)
✔  Image built: harbor.smarttouch.io/myteam/remote-access-service:1.1.0
✔  Image pushed to Harbor
✔  Harbor vulnerability scan: PASS
✔  Manifest updated: k8s/overlays/dev/kustomization.yaml
```

The pipeline automatically commits manifest update to the `k8s/overlays/dev/` overlay. You don't need to update the overlay manually.

### Step 3—Merge the pull request

When all checks pass and the required reviewer has approved, merge the pull request to `main`.

Argo CD detects the manifest change within 3 minutes and begins the deployment.

### Step 4—Monitor the deployment

Track deployment progress:

```bash
stctl status --env dev --service remote-access-service
```

During a rolling update, the output shows the old and new replica counts:

```text
Service:     remote-access-service
Environment: dev
Status:      Deploying
Replicas:    1/2 ready  (1 old, 1 new)
Image:       harbor.smarttouch.io/myteam/remote-access-service:1.1.0
```

Wait until `Replicas: 2/2 ready` before proceeding.

### Step 5—Verify the new version

```bash
stctl status --env dev --service remote-access-service
```

Expected output after a successful deployment:

```text
Service:     remote-access-service
Environment: dev
Status:      Running
Replicas:    2/2 ready
Image:       harbor.smarttouch.io/myteam/remote-access-service:1.1.0
Deployed:    2 minutes ago by github-actions
```

Run a probe to confirm the session broker accepting connections:

```bash
stctl remote-access probe --env dev
```

Expected:

```text
✔  Probe session opened and closed successfully
Broker latency: 18ms
```

---

## Validation

The deployment is successful when:

| Check | Command | Expected |
| --- | --- | --- |
| Service running | `stctl status --env dev --service remote-access-service` | `Status: Running, 2/2 ready` |
| Correct version deployed | Same command | Image tag matches your new version |
| Session broker active | `stctl remote-access probe --env dev` | Probe succeeds |

---

## Troubleshooting

**Deployment stuck in `Deploying` for more than 10 minutes**

Check whether the new pods are starting:

```bash
stctl pods --env dev --service remote-access-service
```

If any pod shows `CrashLoopBackOff` or `ImagePullBackOff`, see [Why is my deployment failing?](../troubleshooting/why-deployment-failing.md).

### Argo CD hasn't picked up the manifest change

Force a sync:

```bash
stctl argocd sync --env dev --app remote-access-service
```

---

## Next steps

- [How do I promote a release to production?](./how-to-promote.md)
- [How do I roll back a deployment?](./how-to-rollback.md)
- [How do I run a canary deployment?](./how-to-canary-deployment.md)
