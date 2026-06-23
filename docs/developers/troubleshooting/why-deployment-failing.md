---
persona: [developer]
task: [deployment, troubleshooting]
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
tags: [deployment, troubleshooting, argo-cd, imagepullbackoff, crashloopbackoff, ssd, remote-access]
related:
  - docs/developers/deploy-release/how-to-deploy-service.md
  - docs/developers/deploy-release/how-to-rollback.md

ai-retrieval-questions:
  - "Why is my deployment failing?"
  - "Why is my service in CrashLoopBackOff?"
  - "Why is my service in ImagePullBackOff?"
  - "Why is Argo CD not syncing my service?"
  - "How do I debug a failed SmartTouch deployment?"
owner: developer-experience-team
reviewer: tech-writing-guild
review-cadence: quarterly
---

# Why is my deployment failing?

> **Keyword:** Why is my deployment failing?

This guide covers the most common reasons a SmartTouch deployment fails and how to resolve each one. Each section follows the pattern: **Symptom → Diagnosis → Resolution → Prevention**.

---

## Quick diagnosis

Run these commands first to identify the failure category.

```bash
# Check Argo CD sync status
stctl deploy status remote-access-service --env staging

# Check pod state
stctl pods remote-access-service --env staging

# Check recent logs
stctl logs remote-access-service --level error --since 10m --env staging
```

Match the output to one of the sections below.

---

## ImagePullBackOff

### Symptom

`stctl pods` shows one or more pods in `ImagePullBackOff` or `ErrImagePull` state.

```text
POD                                  STATUS             RESTARTS   AGE
remote-access-service-78d4b-lx9rp   ImagePullBackOff   0          3m
```

### Diagnosis

The cluster cann't pull the container image from Harbor. Possible causes:

1. The image tag doesn't exist in Harbor—The build pipeline failed or the tag wasn't pushed.
2. Harbor credentials stored in the cluster are expired or incorrect.
3. The image failed the Harbor vulnerability scan and was rejected.

Inspect the pod events to confirm:

```bash
stctl exec remote-access-service -- kubectl describe pod \
  remote-access-service-78d4b-lx9rp --env staging
```

Look for lines starting with `Failed to pull image` or `ImagePullBackoff`.

Check whether the image tag exists in Harbor:

```bash
# List recent tags for the service image
stctl deploy status remote-access-service --env staging --output json \
  | jq '.image_tag'
```

Then verify the tag in Harbor at `https://harbor.<your-domain>/library/remote-access-service`.

### Resolution

**If the image tag doesn't exist:**
Re-run the CI pipeline.
In GitHub Actions, navigate to the workflow run and click **Re-run all jobs**.
The build pushes a new image tag to Harbor on success.

**If Harbor credentials expire:**
Ask a Platform Engineer to rotate the `imagePullSecret` in the cluster.

**If the vulnerability scan rejected the image:**
Review the scan report in Harbor,
address the flagged 'CVEs' in your `Dockerfile` dependencies, and push a new image.

### Prevention

- Add a Harbor scan check to your CI pipeline that fails the build before the image tag is written to the manifest overlay.
- Pin base image versions in your `Dockerfile` so dependency updates are intentional.

---

## CrashLoopBackOff

### Symptoms

`stctl pods` shows one or more pods in `CrashLoopBackOff` state. The `RESTARTS` count increases over time.

```text
POD                                  STATUS              RESTARTS   AGE
remote-access-service-78d4b-lx9rp   CrashLoopBackOff   5          12m
```

### Diagnosis steps

The container starts but exits immediately with a non-zero exit code. Kubernetes restarts it in a loop.

Retrieve the crash logs:

```bash
stctl logs remote-access-service --level error --since 5m --env staging
```

For the previous (crashed) container instance:

```bash
stctl exec remote-access-service -- kubectl logs \
  remote-access-service-78d4b-lx9rp --previous --env staging
```

Common causes in the Remote Access Service:

- Missing required environment variable (for example, `BROKER_URL` not set).
- Secret not mounted—Vault injection failed because the policy path is incorrect.
- Port already in use—another pod is still running and holding the session broker port.
- Health check endpoint not responding within the startup probe timeout.

### Resolution for

**Missing environment variable:** Check that all required keys are present in the SSD `config` block.

```yaml
# smarttouch.yaml
config:
  env:
    BROKER_URL: "wss://broker.smarttouch.local:8443"
    LOG_LEVEL: "info"
    MAX_SESSIONS_PER_DEVICE: "10"
```

Re-apply:

```bash
stctl deploy apply -f smarttouch.yaml --env staging
```

**Secret not mounted:** Verify the Vault path in the SSD `secrets` block matches the path where the secret was written.

```yaml
secrets:
  vault:
    - path: "secret/data/remote-access-service/staging/broker-tls"
      env: BROKER_TLS_CERT
```

Check that the secret exists at this path:

```bash
stctl secrets list remote-access-service --env staging
```

**Port conflict:** Check whether an old pod is still running and holding the port:

```bash
stctl pods remote-access-service --env staging
```

If a stale pod is present, a Platform Engineer can force-delete it.

**Startup probe timeout:** Increase the `startupProbe` timeout in the SSD `deployment` block if your service needs more time to initialize:

```yaml
deployment:
  startupProbe:
    path: /healthz
    initialDelaySeconds: 30
    failureThreshold: 10
```

### Prevention steps

- Test the container image locally with `docker run` before pushing.
- Validate your SSD with `stctl deploy apply --dry-run` before applying to any environment.
- Write startup logs at the first line of your service entrypoint so crash reasons are always visible.

---

## SSD validation error

### Validation symptom

`stctl deploy apply` exits with a non-zero status and prints a validation error. The service isn't updated.

```text
Error: SSD validation failed
  - deployment.replicas: must be greater than 0
  - remote-access.broker-url: required field is missing
```

### Diagnosis method

The `smarttouch.yaml` file contains a field that's missing, has an invalid value, or uses a deprecated key.

### Resolution type

Fix each reported field. Common mistakes:

**`remote-access.broker-url` missing:**

```yaml
remote-access:
  enabled: true
  broker-url: "wss://broker.smarttouch.local:8443"
  protocols:
    - diagnostics
    - shell
```

**`deployment.replicas` set to `0`:**

```yaml
deployment:
  replicas: 2
```

**Deprecated key:** If the error message says `unknown field`, check the [SSD schema reference](../secrets-config/ssd-schema-reference.md) for the current field name.

After fixing the file, validate before applying:

```bash
stctl deploy apply -f smarttouch.yaml --dry-run --env staging
```

### Prevention method

- Run `stctl deploy apply --dry-run` in CI on every pull request before merging.
- Use the SSD JSON Schema in your editor for inline validation—See the [SSD schema reference](../secrets-config/ssd-schema-reference.md).

---

## Argo CD sync failure

### Failure symptom

`stctl deploy status` shows `OutOfSync` or `SyncFailed`. The deployment does not roll out even though the image tag was updated.

```text
Service:      remote-access-service
Environment:  staging
Status:       SyncFailed
Message:      1 error(s) occurred: ConfigMap "remote-access-config" already exists
```

### Diagnosis methods

Argo CD attempted to apply the manifest but encountered a conflict or permission error in the cluster. Common causes:

- A resource (ConfigMap, Service, Deployment) already exists in the cluster with a different owner annotation.
- The Argo CD service account doesn't have permission to update a specific resource type.
- A Helm hook or init container is failing, blocking the sync.

### Resolution methods

**Resource already exists with different owner:** Ask a Platform Engineer to delete the conflicting resource so Argo CD can recreate it under its management.

**Permission error:** Ask a Platform Engineer to review the Argo CD RBAC policy for the service's 'namespace'.

**Sync retry after investigation:**

```bash
# Force a resync through stctl
stctl deploy status remote-access-service --env staging --output json \
  | jq '.argo_app_name'

# Then ask a Platform Engineer to trigger a hard refresh in the Argo CD UI
```

### Resolution for deployment failure

- Don't create cluster resources manually with `kubectl` in environments managed by Argo CD. All resources should originate from Git.
- Annotate resources with `argocd.argoproj.io/managed-by: argocd` if you must create them outside of a GitOps workflow.

---

## Rollback as a last resort

If none of the above resolutions work and the service is unavailable, roll back to the last known good revision immediately:

```bash
stctl rollback remote-access-service --env staging
```

Then investigate the root cause before attempting another deployment. See [How do I roll back a deployment?](../deploy-release/how-to-rollback.md) for the full rollback workflow.

---

## Related

- [How do I deploy a service?](../deploy-release/how-to-deploy-service.md)
- [How do I roll back a deployment?](../deploy-release/how-to-rollback.md)
- [SSD schema reference](../secrets-config/ssd-schema-reference.md)
