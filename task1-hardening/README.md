```markdown
# Task 1 — Workload Hardening

## Overview
Deployed ledger-api + audit-logger on a kind cluster (Kubernetes v1.29.2) with full PCI DSS hardening.

## Architecture
```
payments namespace (PSS: restricted)
├── ledger-api (Deployment)        ← hardened, non-root, sealed secrets
├── audit-logger (Deployment)      ← neighbour service
├── Services (ClusterIP)
└── Ingress (nginx)
```

## Security Controls Applied

| Control | Implementation | Status |
|---------|---------------|--------|
| Non-root container | `runAsNonRoot: true`, `runAsUser: 1000` |
| Read-only filesystem | `readOnlyRootFilesystem: true` |
| Drop capabilities | `capabilities.drop: [ALL]` |
| Seccomp profile | `RuntimeDefault` |
| Privilege escalation | `allowPrivilegeEscalation: false` |
| Secrets management | Sealed Secrets (encrypted in git) |
| Admission control | Kyverno — 4 policies enforced |
| Pod Security Standards | Namespace `restricted` enforced |
| RBAC | Least-privilege ServiceAccount + Role |
| Resource limits | Requests + limits on every container |
| Health probes | Liveness + readiness on every container |

## Kyverno Policies (4)

| Policy | Action | Purpose |
|--------|--------|---------|
| `disallow-root-user` | Enforce | Blocks containers running as root |
| `disallow-latest-tag` | Enforce | Blocks `:latest` image tags |
| `require-readonly-rootfs` | Enforce | Enforces read-only root filesystem |
| `disallow-capabilities` | Enforce | Requires `drop: [ALL]` |

## Secrets Management
- **Tool:** Sealed Secrets (Bitnami)
- Plain secret never committed to git
- Encrypted via `kubeseal` — safe to store in repo
- Decrypted only by Sealed Secrets controller inside cluster

## Proof Screenshots

| Screenshot | Description |
|-----------|-------------|
| `docs/kyverno-block.png` | Kyverno blocking insecure pod (root + :latest) |
| `docs/kyverno-policies.png` | All 4 policies Ready + Enforced |
| `docs/pods-running.png` | audit-logger running in payments namespace |
| `docs/sealed-secret.png` | Sealed secret decrypted by controller |

## Design Decisions
- **Sealed Secrets** over SOPS: simpler K8s-native workflow
- **Kyverno** over OPA/Gatekeeper: readable YAML, no Rego required
- **audit-logger** as neighbour service for multi-service hardening demo
- **emptyDir volumes** for `/tmp` and `/cache` to allow writes with read-only rootFS

## How to Run
```bash
# Prerequisites
kind create cluster --name dodo-cluster --image kindest/node:v1.29.2
kubectl apply -f https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.26.0/controller.yaml
kubectl apply -f https://github.com/kyverno/kyverno/releases/download/v1.12.0/install.yaml

# Deploy
kubectl apply -f k8s/base/namespace.yaml
kubectl apply -f k8s/base/serviceaccount.yaml
kubectl apply -f k8s/base/configmap.yaml
kubectl apply -f secrets/sealed-secret.yaml
kubectl apply -f k8s/base/
kubectl apply -f k8s/policies/

# Verify
kubectl get all -n payments
kubectl get clusterpolicies
kubectl get secret -n payments
```

## Kyverno Block Demo
```bash
# This should be REJECTED by Kyverno
kubectl apply -f - <<EOF
apiVersion: v1
kind: Pod
metadata:
  name: insecure-test
  namespace: payments
spec:
  containers:
    - name: bad-container
      image: nginx:latest
      securityContext:
        runAsUser: 0
EOF
# Expected: Error from server (Forbidden): violates PodSecurity "restricted"
```
```
