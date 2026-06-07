# SmartTouch Cloud Platform

---

## Overview

SmartTouch Cloud Platform is an end-to-end IoT developer platform that gives engineering teams everything they need to deploy, manage, monitor, and scale IoT services — without managing raw infrastructure.

At its core, SmartTouch bridges the gap between IoT devices in the field and the cloud services that process their data. A device sends a temperature reading; SmartTouch routes it through a secure MQTT gateway, validates and stores it, evaluates it against configured policies, and makes it observable through a unified dashboard — all through platform primitives that teams configure rather than build.

SmartTouch is designed for three roles:

- **Developers** use SmartTouch to deploy IoT services, connect devices, and observe their workloads — without needing to understand Kubernetes or infrastructure.
- **Platform Engineers** use SmartTouch to provision and operate the underlying cluster, pipelines, and observability stack that developers build on.
- **Administrators** use SmartTouch to manage access, enforce governance, and maintain the audit trail across teams and environments.

---

## Platform Stack

Each layer of the SmartTouch stack has a specific role. Understanding what each technology does helps you find the right part of the platform for your task.

| Layer | Technology | What it does for you |
|---|---|---|
| **Orchestration** | Kubernetes (EKS / GKE / self-managed) | Runs your IoT services as containers, handles scaling, restarts, and scheduling. Developers deploy via SSD files — no raw Kubernetes YAML required. |
| **Infrastructure as Code** | Terraform + Terragrunt | Platform Engineers provision and update all environments (dev, staging, prod) through code. Every cluster, network, and storage resource is defined, versioned, and reproducible. |
| **CI/CD** | GitHub Actions + Argo CD | GitHub Actions builds and tests your code on every push. Argo CD watches Git for changes and automatically reconciles the cluster state — no manual `kubectl apply`. |
| **Observability** | OpenTelemetry → Prometheus + Grafana + Loki + Jaeger | Every service emits metrics, logs, and traces through a single OpenTelemetry pipeline. Grafana surfaces all three in one place so you can go from alert to root cause without switching tools. |
| **IoT Gateway** | EMQX MQTT broker + Edge Agent | The entry point for device data. EMQX handles millions of device connections over MQTT with TLS. The Edge Agent runs on constrained hardware and buffers data through intermittent connectivity. |
| **Service Mesh** | Istio | Encrypts all traffic between services automatically (mTLS), enforces access policies, and provides traffic management for canary and blue/green deployments — without changes to application code. |
| **Secrets Management** | HashiCorp Vault | Issues short-lived credentials to services at runtime. No long-lived passwords in environment variables. Developers request secrets through the SSD; Vault delivers them directly to pods. |
| **Container Registry** | Harbor | Stores and scans container images before they are deployed. All images must pass a vulnerability scan before Argo CD will deploy them to staging or production. |

---

## Environments and the GitHub PR Workflow

SmartTouch has three environments. Each maps to a stage of the pull request workflow.

```
dev  →  staging  →  prod
```

### dev — for active development

Every developer has access to the `dev` environment. It is the first place a service runs on the platform after a commit is pushed.

**How it works:**
1. You push a branch and open a pull request.
2. GitHub Actions runs lint, unit tests, builds the container image, and pushes it to Harbor.
3. The image tag is automatically updated in the `dev` manifest overlay.
4. Argo CD detects the change and deploys the new version to `dev` within 2 minutes.
5. No approval is required — `dev` deploys on every push to a feature branch.

### staging — for integration validation

`staging` mirrors production configuration. It is the gate before any change reaches live users.

**How it works:**
1. You merge your pull request to `main`.
2. GitHub Actions promotes the verified image tag to the `staging` manifest overlay.
3. Argo CD deploys to `staging` automatically on merge to `main`.
4. Automated integration tests and smoke tests run against `staging`.
5. A passing staging deployment is the required condition for a production release.

### prod — for live services

`prod` is deployed only from a tagged release. It requires a manual pull request approval from a Platform Engineer or Administrator.

**How it works:**
1. A release is tagged (e.g., `v1.2.0`) on `main`.
2. GitHub Actions promotes the image tag to the `prod` manifest overlay and opens a pull request against the `prod` branch.
3. A Platform Engineer or Administrator reviews and approves the PR.
4. On merge, Argo CD deploys to `prod`.
5. Argo CD monitors for configuration drift — if the live cluster diverges from Git, it alerts and can auto-remediate.

All three environments are isolated Terraform workspaces with independent state. Promoting between environments is always a Git operation — never a direct cluster command.
