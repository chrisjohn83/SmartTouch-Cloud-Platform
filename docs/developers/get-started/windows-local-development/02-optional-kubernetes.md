---
persona: [developer]
task: [local-development, kubernetes]
product: [smarttouch-cloud]
difficulty: intermediate
status: published
version: "2.0"
platform-version: "2.x"
tags: [windows, powershell, kubernetes, optional]
sequence: 2
part-of: windows-local-development
---

# Optional: configure Kubernetes on Windows

Kubernetes is not required for the local V2 API sandbox. Complete this page only when an administrator has given you access to a real Kubernetes cluster.

## 1. Install kubectl

```powershell
winget install --exact --id Kubernetes.kubectl
```

Open a new terminal and verify the installation:

```powershell
kubectl version --client
```

## 2. Install the supplied kubeconfig

Obtain a kubeconfig from your SmartTouch administrator and save it to:

```text
C:\Users\<your-user>\.kube\config
```

List the available contexts and select the assigned context:

```powershell
kubectl config get-contexts
kubectl config use-context <context-name>
```

## 3. Verify access

```powershell
kubectl get namespaces
kubectl get pods --namespace smarttouch-remote-access
```

If you receive an authentication or authorization error, contact the cluster administrator. The local repository cannot create production cluster credentials.

Continue to [Run the portal and API locally](./03-run-portal-and-api.md).
