---
persona: [developer]
task: [secrets, remote-access, security]
product: [smarttouch-cloud]
difficulty: intermediate
status: published
version: "1.0"
platform-version: "1.x"
last-reviewed: "2026-06-06"
locale: 'en-US'
translation-status: source
translated-from: ""
accessibility:
  reviewed: false
  images-have-alt-text: true
  color-independent: true
  has-text-diagrams: true
tags: [secrets, vault, hashicorp, tls, certificates, remote-access]
related:
  - docs/developers/secrets-config/how-to-environment-config.md
  - docs/developers/secrets-config/ssd-schema-reference.md
ai-retrieval-questions:
  - "How do I manage secrets securely on SmartTouch?"
  - "How do I store TLS certificates in Vault?"
  - "How does the Remote Access Service access secrets at runtime?"
  - "How do I rotate secrets for the Remote Access Service?"
owner: developer-experience-team
reviewer: tech-writing-guild
review-cadence: quarterly
---

# How do I manage secrets securely?

> **Keyword:** How do I manage secrets securely on SmartTouch?

SmartTouch uses HashiCorp Vault to manage all secrets. Services never receive secrets as environment variables or Kubernetes Secrets in plain text. Instead, the platform injects short-lived credentials directly into the pod at runtime via the Vault Agent Injector.

---

## Goal

Store the Remote Access Service TLS certificate and broker authentication credentials in Vault and configure the SSD to inject them at runtime.

---

## Prerequisites

- `stctl` installed and authenticated
- The Remote Access Service SSD created—See [Create the Remote Access Service SSD](../get-started/deploy-first-iot-service/01-create-service-spec.md)
- Administrator or Platform Engineer role (required to create Vault policies)

---

## How Vault secret injection works

```text
Pod starts
        ↓
Vault Agent Injector intercepts the pod spec
        ↓
Agent authenticates to Vault using the pod's Kubernetes Service Account
        ↓
Agent fetches the secrets specified in the SSD
        ↓
Agent writes secrets to a tmpfs volume at /vault/secrets/
        ↓
Service reads secrets from the file path
```

Secrets are written to memory-only storage ('tmpfs'). They're never written to disk and are removed when the pod stops.

---

## Steps

### Step 1—Store a secret in Vault

Use `stctl` to write a secret to your service's Vault path:

```bash
stctl secrets set \
  --service remote-access-service \
  --env dev \
  --key broker-tls-cert \
  --file sensor-001.crt
```

```bash
stctl secrets set \
  --service remote-access-service \
  --env dev \
  --key broker-tls-key \
  --file sensor-001.key
```

Expected output:

```text
✔  Secret stored
Path:    secret/remote-access-service/dev/broker-tls-cert
Version: 1
```

### Step 2—List secrets for your service

```bash
stctl secrets list --service remote-access-service --env dev
```

Expected:

```text
KEY                VERSION   LAST UPDATED
broker-tls-cert    1         2026-06-06T14:00:00Z
broker-tls-key     1         2026-06-06T14:00:01Z
```

### Step 3—Reference secrets in the SSD

Add a `secrets` block to `smarttouch.yaml`:

```yaml
secrets:
  vault-path: "secret/remote-access-service/{{env}}"
  inject:
    - key: broker-tls-cert
      mount-path: /vault/secrets/broker.crt
    - key: broker-tls-key
      mount-path: /vault/secrets/broker.key
```

The `{{env}}` placeholder is replaced at deploy time with the target environment (`dev`, `staging`, `prod`). This means the same SSD works across all environments—Each environment reads from its own Vault path.

### Step 4—Read the secret in your service code

The secret is available at the file path specified in `mount-path`:

```javascript
// Node.js — read the injected TLS certificate
const fs = require('fs');
const cert = fs.readFileSync('/vault/secrets/broker.crt');
const key  = fs.readFileSync('/vault/secrets/broker.key');
```

```python
# Python — read the injected TLS certificate
with open('/vault/secrets/broker.crt') as f:
    cert = f.read()
with open('/vault/secrets/broker.key') as f:
    key = f.read()
```

### Step 5—Rotate a secret

When a certificate expires or a key is compromised, update the secret in Vault and trigger a pod restart to pick up the new version:

```bash
stctl secrets set \
  --service remote-access-service \
  --env dev \
  --key broker-tls-cert \
  --file sensor-001-renewed.crt
```

```bash
stctl restart --env dev --service remote-access-service
```

The pods restart one at a time (rolling restart). Each new pod fetches the updated secret from Vault on startup.

---

## Validation

Secret injection is working when:

```bash
stctl exec --env dev --service remote-access-service \
  -- ls /vault/secrets/
```

Expected:

```text
broker.crt
broker.key
```

---

## Troubleshooting

**`/vault/secrets/` directory is empty after pod start**

The Vault Agent Injector didn't run. Check whether the injector is enabled for your 'namespace':

```bash
kubectl get namespace team-myteam -o yaml | grep vault-injection
```

If the annotation `vault.hashicorp.com/agent-inject: "true"` is missing, contact your Platform Engineer to enable Vault injection for your namespace.

**`permission denied` when reading the secret file**

The secret file is owned by the vault-agent user. If your service runs as a different user, add your service's UID to the Vault injection annotation. Contact your Platform Engineer.

---

## Next steps

- [How do I use environment-specific 'config'?](./how-to-environment-config.md)
- [What's the SSD schema?](./ssd-schema-reference.md)
