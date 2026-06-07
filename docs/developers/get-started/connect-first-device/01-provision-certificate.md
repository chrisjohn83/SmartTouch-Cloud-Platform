---
persona: [developer]
task: [device-connection, remote-access, security]
product: [smarttouch-cloud]
difficulty: beginner
status: published
version: "1.0"
platform-version: "1.x"
last-reviewed: "2026-06-06"
tags: [device, certificate, remote-access, tls, provisioning, x509]
sequence: 1
part-of: connect-first-device
related:
  - docs/developers/get-started/connect-first-device/index.md
  - docs/developers/get-started/connect-first-device/02-install-remote-access-agent.md

ai-retrieval-questions:
  - "How do I provision a device certificate for remote access?"
  - "What certificate does a device need for SmartTouch remote access?"
  - "How do I create a device identity for remote access?"
  - "How do I register a device with the Remote Access Service?"
  - "How do I generate a TLS certificate for a SmartTouch device?"

owner: developer-experience-team
reviewer: tech-writing-guild
review-cadence: quarterly
---

# Provision a device certificate for remote access

> **Keyword:** How do I provision a device certificate for remote access?
> **Part of:** [Connect a device for remote access](./index.md) — Step 1 of 3

Every device that connects to the SmartTouch Remote Access Service authenticates with an X.509 client certificate. This certificate identifies the device to the session broker and determines which sessions it can accept. This tutorial provisions the certificate and registers the device as remote-access-enabled.

---

## Goal

Provision a TLS certificate for `sensor-001` and register it with the Remote Access Service in your `dev` environment.

---

## Prerequisites

- Remote Access Service deployed and healthy — run `stctl remote-access status --env dev` and confirm `Session broker: ready`
- `stctl` authenticated
- OpenSSL installed

---

## Steps

### Step 1 — Create the device identity

```bash
stctl device create \
  --id sensor-001 \
  --type temperature-sensor \
  --remote-access \
  --env dev
```

The `--remote-access` flag registers this device with the Remote Access Service in addition to the device registry. Without it, the session broker will reject connection attempts from the device.

Expected output:

```text
✔  Device created
Device ID:          sensor-001
Type:               temperature-sensor
Remote access:      enabled
Status:             pending-certificate
```

### Step 2 — Generate a private key on the device

The private key must be generated on the device and must never leave it. If you are provisioning remotely (before the device is deployed), generate the key on any machine and transfer it to the device over a secure channel before installation.

```bash
openssl genrsa -out sensor-001.key 2048
chmod 600 sensor-001.key
```

### Step 3 — Create a Certificate Signing Request

```bash
openssl req -new \
  -key sensor-001.key \
  -out sensor-001.csr \
  -subj "/CN=sensor-001/O=smarttouch/OU=remote-access"
```

The `OU=remote-access` extension tells the SmartTouch certificate authority to issue a certificate with the remote access key usage extension. Certificates without this extension are accepted for MQTT connections but rejected by the Remote Access Service.

### Step 4 — Sign the certificate

```bash
stctl device certificate sign \
  --device-id sensor-001 \
  --csr sensor-001.csr \
  --out sensor-001.crt \
  --env dev
```

Expected output:

```text
✔  Certificate signed
Certificate: sensor-001.crt
Expires:     2027-06-06
Key usage:   clientAuth, remoteAccess
CA bundle:   Downloaded to smarttouch-ca.crt
```

Confirm `Key usage` includes `remoteAccess`. If it shows only `clientAuth`, the CSR `OU` was not set correctly — regenerate the CSR with `OU=remote-access` and re-sign.

### Step 5 — Verify the device is registered for remote access

```bash
stctl device status --id sensor-001 --env dev
```

Expected output:

```text
Device ID:      sensor-001
Status:         active
Remote access:  enabled
Certificate:    valid (expires 2027-06-06, key usage: remoteAccess)
Agent:          not installed
Last seen:      never
```

`Agent: not installed` is expected — the Remote Access Agent has not been installed yet. You will do that in the next tutorial.

---

## Validation

```bash
stctl device status --id sensor-001 --env dev
# Remote access: enabled
# Certificate: valid ... key usage: remoteAccess
```

---

## Troubleshooting

**`Key usage: clientAuth` only (remoteAccess missing)**
The CSR was generated without `OU=remote-access`. Delete the existing CSR, regenerate it with the correct `-subj` line, and re-sign:

```bash
rm sensor-001.csr
openssl req -new -key sensor-001.key -out sensor-001.csr \
  -subj "/CN=sensor-001/O=smarttouch/OU=remote-access"
stctl device certificate sign --device-id sensor-001 --csr sensor-001.csr --out sensor-001.crt --env dev
```

**`Error: remote access not enabled for this device type`**
Your organisation's policy restricts which device types can have remote access enabled. Contact your Administrator to add `temperature-sensor` to the allowed types.

**`Error: device ID already exists`**
Run `stctl device status --id sensor-001 --env dev` to check the existing device. If it does not have `Remote access: enabled`, delete and recreate it with the `--remote-access` flag.

---

## Next steps

`sensor-001` has a valid certificate with remote access key usage and is registered with the Remote Access Service.

→ Continue to **Step 2:** [Install the Remote Access Agent](./02-install-remote-access-agent.md)
