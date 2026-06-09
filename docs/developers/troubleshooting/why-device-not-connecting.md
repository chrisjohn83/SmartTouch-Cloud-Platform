---
persona: [developer]
task: [remote-access, troubleshooting, device-connection]
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
tags: [device, remote-access, troubleshooting, certificate, agent, broker, websocket, firewall]
related:
  - docs/developers/get-started/connect-first-device/01-provision-certificate.md
  - docs/developers/get-started/connect-first-device/02-install-remote-access-agent.md
  - docs/developers/api-reference/stctl-cli-reference.md
  - docs/developers/api-reference/rest-api.md
ai-retrieval-questions:
  - "Why is my device not connecting?"
  - "Why is the Remote Access Agent offline?"
  - "Why can I not open a remote access session to my device?"
  - "Why does stctl remote-access open fail?"
  - "How do I debug a device that isn't connecting to SmartTouch?"
owner: developer-experience-team
reviewer: tech-writing-guild
review-cadence: quarterly
---

# Why is my device not connecting?

> **Keyword:** Why is my device not connecting?

This guide covers the most common reasons a device doesn't appear online in SmartTouch or a remote access session fails to open.

---

## Quick diagnosis

Run these commands from your workstation to identify the problem quickly.

```bash
# Check whether the device is registered and its agent status
stctl device agent-status sensor-001

# Try opening a diagnostics session
stctl remote-access open sensor-001 --protocol diagnostics
```

Match the output to one of the sections below.

**On the device itself**, check the agent process:

```bash
# On the device — check whether the agent is running
systemctl status smarttouch-agent

# On the device — view the last 50 agent log lines
journalctl -u smarttouch-agent -n 50
```

---

## Agent isn't running

### Symptom: Agent shows offline

`stctl device agent-status` shows `offline`. `systemctl status smarttouch-agent` on the device shows the service as `inactive` or `failed`.

```text
Device:        sensor-001
Agent status:  offline
Last seen:     3h ago
```

### Diagnosis

The Remote Access Agent process has stopped or failed to start.

On the device, check the service status and recent logs:

```bash
systemctl status smarttouch-agent
journalctl -u smarttouch-agent --since "1 hour ago" -n 100
```

Common failure messages:

| Log message | Cause |
| --- | --- |
| `certificate file not found: /etc/smarttouch/device.crt` | Certificate path in `agent.yaml` is wrong or the file was deleted |
| `failed to connect to broker: dial tcp: connection refused` | Broker URL is unreachable |
| `certificate has expired` | Device certificate passed its expiry date |
| `x509: certificate signed by unknown authority` | CA bundle is missing or incorrect |

### Resolution

**Start the agent:**

```bash
systemctl start smarttouch-agent
systemctl enable smarttouch-agent
```

**If the agent starts but immediately stops**, check the log message and follow the relevant section below.

**If the unit file is missing**, reinstall the agent—see [Install the Remote Access Agent](../get-started/connect-first-device/02-install-remote-access-agent.md).

### Prevention

- Enable `smarttouch-agent` with `systemctl enable` during provisioning so it starts on boot.
- Add a systemd watchdog restart policy to the agent unit file:

  ```ini
  [Service]
  Restart=on-failure
  RestartSec=10s
  ```

---

## Certificate error

### Symptom: Certificate validation fails

The agent is running but the device doesn't appear online. Agent logs contain messages such as `certificate has expired`, `certificate file not found`, or `x509: certificate signed by unknown authority`.

### Diagnosys

The device certificate used to authenticate the WebSocket connection to the broker is missing, expired, or was signed by an authority the broker doesn't trust.

**Check the certificate on the device:**

```bash
# View the certificate subject and expiry
openssl x509 -in /etc/smarttouch/device.crt -noout -subject -dates
```

Expected output:

```text
subject=CN=sensor-001, OU=remote-access, O=smarttouch
notBefore=Jun  8 00:00:00 2026 GMT
notAfter=Jun  8 00:00:00 2027 GMT
```

**Verify the `OU=remote-access` extension is present.** Without this extension, the broker rejects the certificate.

**Check the CA bundle the agent uses:**

```bash
cat /etc/smarttouch/ca-bundle.crt
```

This file must contain the SmartTouch platform CA certificate. Compare its fingerprint with the one shown in the SmartTouch Console under **Settings → Certificate Authorities**.

### Solution

**Expired certificate:** Provision a new certificate — see [Provision a device certificate for remote access](../get-started/connect-first-device/01-provision-certificate.md). After replacing the certificate files, restart the agent:

```bash
systemctl restart smarttouch-agent
```

**Missing `OU=remote-access` extension:** The certificate was provisioned without the required CSR extension. Provision a new certificate with the correct CSR:

```bash
openssl req -new -key /etc/smarttouch/device.key \
  -out /tmp/device.csr \
  -subj "/CN=sensor-001/OU=remote-access/O=smarttouch"
```

Submit the CSR and install the signed certificate at `/etc/smarttouch/device.crt`.

**Wrong or missing CA bundle:** Copy the platform CA certificate from the SmartTouch Console and write it to `/etc/smarttouch/ca-bundle.crt`. Restart the agent.

### Prevent certificate failures

- Set a calendar reminder 30 days before the certificate expiry date shown in `stctl device get <device_id>`.
- Automate certificate renewal using the SmartTouch certificate rotation API — see [How do I manage secrets securely?](../secrets-config/how-to-manage-secrets.md).

---

## Cann't reach the broker

### Symptom: Broker connection fails

The agent is running and the certificate is valid, but agent logs show `connection refused`, `i/o timeout`, or `no route to host` when connecting to the broker URL.

### Analysis

The device cann't establish the outbound WebSocket connection to the Remote Access Service broker. The broker URL is configured in `/etc/smarttouch/agent.yaml`.

**Check the broker URL in the agent configuration:**

```bash
cat /etc/smarttouch/agent.yaml
```

The `broker-url` field must use the `wss://` scheme and port 8443:

```yaml
broker-url: "wss://broker.smarttouch.local:8443"
```

**Test connectivity from the device:**

```bash
# Test TCP connectivity to the broker port
nc -zv broker.smarttouch.local 8443

# Test TLS handshake
openssl s_client -connect broker.smarttouch.local:8443 \
  -cert /etc/smarttouch/device.crt \
  -key /etc/smarttouch/device.key \
  -CAfile /etc/smarttouch/ca-bundle.crt
```

**Diagnose the failure:**

| Test result | Cause |
| --- | --- |
| `nc` fails with `Connection refused` | Broker service is down or the port isn't open |
| `nc` fails with `No route to host` | Network routing or firewall issue |
| `nc` succeeds but TLS fails | Certificate mismatch or CA bundle problem |
| `nc` times out | Firewall blocking outbound port 8443 |

### Solution steps

**Wrong broker URL:** Update `/etc/smarttouch/agent.yaml` with the correct broker URL. The correct value is shown in `stctl device get sensor-001` under `remote_access.broker_url`. Restart the agent after editing.

**Firewall blocking outbound port 8443:** The Remote Access Agent requires outbound TCP/WebSocket access on port 8443. Work with your network administrator to allow outbound connections to the broker host name on port 8443.

The agent doesn't require any inbound ports—all sessions are initiated via the outbound WebSocket connection.

**Broker service is down:** Check the broker health from your workstation:

```bash
stctl status --env staging | grep -i broker
```

If the broker shows `unhealthy`, contact your Platform Engineer.

### Prevent connectivity issues

- Test broker connectivity as part of device provisioning before the device is deployed to the field.
- Configure device network policy to explicitly allow outbound connections to the broker host name on port 8443.
- Monitor agent connectivity with `stctl device agent-status` or via the SmartTouch Console fleet view.

---

## 'stctl' Remote-access open fails

### Symptom: Session open request fails

The device shows `online` in `stctl device agent-status`, but `stctl remote-access open` fails with an error.

Common error messages:

```text
Error: forbidden — your role doesn't permit shell sessions
Error: conflict — a session is already open for this device on this protocol
Error: unprocessable_entity — device agent is offline
```

### Analysis steps

**`forbidden`:** You are requesting a protocol your role doesn't permit. See the protocol permission table:

| Protocol | Minimum role |
| --- | --- |
| `diagnostics` | developer |
| `shell` | platform-engineer |
| `file-transfer` | administrator |

**`conflict`:** Another session of the same protocol is already open to this device. Only one session per protocol per device is allowed at a time.

**`unprocessable_entity`:** The device appeared online when you checked but went offline between the check and the session open attempt. This can happen if the device has an intermittent network connection.

### Remediation

**`forbidden`:** Use a protocol your role permits. As a developer, use `--protocol diagnostics`.

**`conflict`:** List open sessions and close the existing one:

```bash
stctl remote-access list --device sensor-001 --status open

stctl remote-access close <session_id>
```

Then retry:

```bash
stctl remote-access open sensor-001 --protocol diagnostics
```

**`unprocessable_entity`:** Wait 30 seconds for the agent to reconnect and retry. If the device continues to drop connection, check the agent logs on the device for network errors.

### Best practices

- Build session take apart into your automation scripts so sessions are always closed after use.
- Use `stctl remote-access list --device <id> --status open` to check for existing sessions before opening a new one.

---

## Device not registered

### Symptom: Device not found

`stctl device get sensor-001` returns a `404 not_found` error. The device ID doesn't exist in the platform.

```text
Error: device not found: sensor-001
```

### Why this happens

The device was never registered with the platform, or it was registered under a different device ID.

### Register the device

**List all registered devices** to check whether the device exists under a different ID:

```bash
stctl device list --status offline
```

**If the device isn't listed at all**, it hasn't been registered.

To register a new device:
provision its certificate with the correct `CN` matching the device ID you want to use—see [Provision a device certificate for remote access](../get-started/connect-first-device/01-provision-certificate.md).

The device is registered automatically the first time the Remote Access Agent successfully connects to the broker using its certificate.

### Best practice

- Keep a record of all device IDs and their corresponding certificate 'CNs'.
- Use a consistent naming convention for device IDs (for example, `<fleet>-<device-type>-<serial>`).

---

## Related

- [Provision a device certificate for remote access](../get-started/connect-first-device/01-provision-certificate.md)
- [Install the Remote Access Agent](../get-started/connect-first-device/02-install-remote-access-agent.md)
- [SmartTouch REST API reference](../api-reference/rest-api.md)
- ['stctl' CLI reference](../api-reference/stctl-cli-reference.md)
