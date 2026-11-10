# Configuration and secrets on Windows

The local V2 sandbox supports non-sensitive service configuration in Deployment API requests. It does not include Vault or another production secret manager.

Use this section to:

- set local values with PowerShell environment variables;
- send non-sensitive configuration through the Deployment API;
- keep credentials out of source control and API payloads; and
- understand the V2 deployment request fields.

For local API calls, use the development bearer token `demo-token`. Replace it with an approved identity and secret-management solution before production deployment.
