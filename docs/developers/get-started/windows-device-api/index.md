# Test the Device API on Windows

Use PowerShell or the V2 API Playground to register and inspect devices in the local sandbox.

## Before you begin

- Start the V2 API on port `8090`.
- Start MkDocs on port `8001` if you want to use the Playground.
- Use bearer token `demo-token`.

## Steps

1. [Register a test device](./01-register-device.md).
2. [Inspect device details](./02-inspect-device.md).
3. [Verify agent status](./03-verify-agent-status.md).

The sandbox is in-memory. Restarting the API restores `sensor-001` and `sensor-002` and removes devices you registered.
