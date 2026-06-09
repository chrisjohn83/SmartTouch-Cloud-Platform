---
persona: [developer]
task: [local-development, remote-access, kubernetes]
product: [smarttouch-cloud]
difficulty: beginner
status: published
version: "1.0"
platform-version: "1.x"
last-reviewed: "2026-06-06"
tags: [kubernetes, kubectl, kubeconfig, remote-access, namespace, session-broker]
sequence: 2
part-of: set-up-local-development
related:
  - docs/developers/get-started/set-up-local-development/01-install-stctl.md
  - docs/developers/get-started/set-up-local-development/03-run-service-locally.md

ai-retrieval-questions:
  - "How do I configure kubectl for SmartTouch remote access?"
  - "Which Kubernetes namespace runs the Remote Access Service?"
  - "How do I inspect Remote Access Service pods in Kubernetes?"
  - "How do I connect kubectl to the SmartTouch dev cluster?"

owner: developer-experience-team
reviewer: tech-writing-guild
review-cadence: quarterly
---

# Configure your local Kubernetes context

> **Keyword:** How do I configure kubectl for SmartTouch remote access?
> **Part of:** [Set up local development](./index.md) — Step 2 of 3

The Remote Access Service runs in a dedicated Kubernetes namespace. Configuring your local Kubernetes context gives you direct access to session broker pod logs, metrics, and events — essential for debugging connection issues and session failures.

---

## Goal

Configure `kubectl` to reach the SmartTouch `dev` cluster and confirm you can view the Remote Access Service namespace.

---

## Prerequisites

- Completed [Install the SmartTouch CLI](./01-install-stctl.md)
- `stctl auth status` returns your email

---

## Steps

### Step 1 — Install kubectl

### macOS

```bash
brew install kubectl
```

### Linux

```bash
curl -LO "https://dl.k8s.io/release/$(curl -sSL https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl && sudo mv kubectl /usr/local/bin/
```

Verify:

```bash
kubectl version --client
```

### Step 2 — Fetch the kubeconfig

```bash
stctl kubeconfig get --env dev
```

Expected output:

```text
✔  Fetched credentials for env: dev
✔  Merged into ~/.kube/config
✔  Context added: smarttouch-dev
```

### Step 3 — Set the active context

```bash
kubectl config use-context smarttouch-dev
```

### Step 4 — Verify access to the Remote Access Service namespace

The Remote Access Service runs in `smarttouch-remote-access`. You have read-only access to this namespace.

```bash
kubectl get pods --namespace smarttouch-remote-access
```

Expected output lists the running broker pods:

```text
NAME                                       READY   STATUS    RESTARTS
remote-access-service-6c8d4f-ql7rn         1/1     Running   0
remote-access-service-6c8d4f-xm4pk         1/1     Running   0
```

If the namespace is empty, the Remote Access Service has not been deployed yet. Complete [Deploy the Remote Access Service](../deploy-first-iot-service/index.md) first.

### Step 5 — View broker logs directly

During development, reading broker logs helps diagnose session failures:

```bash
kubectl logs --namespace smarttouch-remote-access \
  --selector app=remote-access-service \
  --follow
```

Press `Ctrl+C` to stop streaming.

### Step 6 — Set a default namespace for your team

```bash
kubectl config set-context --current --namespace team-myteam
```

---

## Remote Access namespace layout

| Namespace | Contains | Your access |
| --- | --- | --- |
| `team-<name>` | Your deployed services | Full read/write |
| `smarttouch-remote-access` | Remote Access Service, session proxy | Read only |
| `smarttouch-audit` | Audit log collector | No direct access — use `stctl remote-access audit` |

---

## Validation

```bash
kubectl config current-context
# Returns: smarttouch-dev

kubectl get pods --namespace smarttouch-remote-access
# Returns remote-access-service pods in Running state
```

---

## Troubleshooting

**`Error from server (Forbidden)` on `smarttouch-remote-access`**
Your account is missing the `developer` role. Contact your Administrator to confirm your role assignment.

**Namespace shows no pods**
Deploy the Remote Access Service first: [Deploy the Remote Access Service](../deploy-first-iot-service/index.md).

**`Unable to connect to the server`**
Connect to your organisation's VPN if required, then retry.

---

## Next steps

→ Continue to **Step 3:** [Run the Remote Access Service locally](./03-run-service-locally.md)
