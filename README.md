```markdown
# Dodo Payments — DevSecOps Assessment

**Candidate:** Sri Vaishnavi Nunna  
**Role:** Security & DevOps Engineer  
**Repo:** https://github.com/SriBoo/dodo-devsecops

---

## Overview

This repository contains my solution to the Dodo Payments DevSecOps assessment.
All four tasks have been completed with working implementations, screenshots as proof,
and documentation explaining design decisions.

---

## Task 1 — Workload Hardening ✅

**What was done:**
- Deployed `ledger-api` + `audit-logger` on kind cluster (Kubernetes v1.29.2)
- Full PCI DSS hardening applied to all workloads
- Kyverno admission policies blocking insecure deployments
- Sealed Secrets for secret management (no plaintext in git)

**Key Controls:**
| Control | Implementation |
|---------|---------------|
| Non-root container | `runAsNonRoot: true`, `runAsUser: 1000` |
| Read-only filesystem | `readOnlyRootFilesystem: true` |
| Drop capabilities | `capabilities.drop: [ALL]` |
| Seccomp | `RuntimeDefault` profile |
| Secrets | Sealed Secrets — encrypted in git |
| Admission | Kyverno — 4 policies (root, :latest, readOnlyRootFS, capabilities) |
| Pod Security | Namespace `restricted` PSS enforced |
| RBAC | Least-privilege ServiceAccount + Role |

**Proof:** `task1-hardening/docs/` — Kyverno blocking insecure pod, sealed secret, pods running

→ [task1-hardening/README.md](./task1-hardening/README.md)

---

## Task 2 — Secure CI/CD Pipeline ✅

**What was done:**
- Rebuilt CI/CD pipeline with security at every stage
- Fixed 3 vulnerabilities in original app (SSRF, YAML injection, PAN exposure)
- Hardened Dockerfile (python:3.11-slim, non-root user, multi-stage build)
- Updated all dependencies to latest secure versions

**Pipeline Stages:**
| Stage | Tool | Result |
|-------|------|--------|
| Secrets Scan | Gitleaks | ✅ No leaks detected |
| SAST | Semgrep | ✅ OWASP rules applied |
| Dependency CVE | Trivy | ✅ CVEs flagged |
| Build Image | Docker | ✅ Pushed to GHCR |
| Image CVE Scan | Trivy | ✅ Image scanned |
| Sign | Cosign | ⚠️ OIDC limitation (see note) |

**Note on Cosign:** Cosign keyless signing requires GitHub OIDC token.
Sign step fails due to free-tier OIDC configuration. Architecture is
correctly implemented — would work with org-level OIDC permissions.

**Proof:** `task2-cicd/docs/` — pipeline runs, GHCR image published

→ [task2-cicd/README.md](./task2-cicd/README.md)

---

## Task 3 — Service Mesh & Zero-Trust ✅

**What was done:**
- Installed Istio 1.21.0 on kind cluster
- Enforced mTLS STRICT across payments namespace
- Default-deny AuthorizationPolicy with identity-based allows
- NetworkPolicy as defence-in-depth underneath Istio
- Verified sidecar injection (2/2 pods) and mTLS blocking (exit code 56)

**Security Layers:**
| Layer | Implementation |
|-------|---------------|
| mTLS | PeerAuthentication STRICT — plaintext refused |
| AuthZ | Default-deny + SPIFFE identity-based allows |
| NetworkPolicy | Node-level default-deny + explicit allows |
| Sidecar | istio-proxy injected in all pods (2/2) |

**Proof:** `task3-mesh/docs/` — mTLS block proof (exit code 56), sidecar 2/2, policies applied

→ [task3-mesh/README.md](./task3-mesh/README.md)

---

## Task 4 — Reconnaissance & Penetration Testing ✅

**What was done:**

**Part A — Passive Recon (dodopayments.com):**
- Certificate transparency via crt.sh — discovered 5 subdomains
- Shodan — 21 results, nginx/1.24.0, AWS + Cloudflare
- VirusTotal — Gridinsoft flagged suspicious

**Subdomains Found:**
| Subdomain | Risk |
|-----------|------|
| test.checkout.dodopayments.com | MEDIUM — test env exposed |
| metrics.dodopayments.com | LOW — metrics exposed |
| tools.dodopayments.com | MEDIUM — internal tools exposed |

**Part B — Penetration Test (ledger-api-assignment):**
| # | Finding | Severity | Fixed |
|---|---------|----------|-------|
| 1 | Hardcoded Secrets | CRITICAL | ✅ Sealed Secrets |
| 2 | SSRF | CRITICAL | ✅ URL allowlist |
| 3 | YAML Injection (RCE) | HIGH | ✅ yaml.safe_load() |
| 4 | PAN Data Exposure | HIGH | ✅ Masked PANs |
| 5 | EOL Dependencies | MEDIUM | ✅ Updated versions |

**Proof:** `task4-pentest/` — recon screenshots, pentest report with PoCs

→ [task4-pentest/README.md](./task4-pentest/README.md)

---

## Repository Structure

```
dodo-devsecops/
├── README.md
├── ledger-api-src/              ← Original assignment repo (hardened)
├── task1-hardening/
│   ├── k8s/base/                ← Hardened K8s manifests
│   ├── k8s/policies/            ← Kyverno policies
│   ├── secrets/                 ← Sealed secrets
│   └── docs/                   ← Screenshots
├── task2-cicd/
│   ├── .github/workflows/       ← CI/CD pipeline
│   └── docs/                   ← Screenshots
├── task3-mesh/
│   ├── istio/                   ← PeerAuthentication + AuthorizationPolicy
│   ├── networkpolicy/           ← NetworkPolicy
│   └── docs/                   ← Screenshots
└── task4-pentest/
    ├── recon/                   ← Recon report + screenshots
    └── pentest/                 ← Pentest report + screenshots
```

---

## How to Run

```bash
# Prerequisites
kind create cluster --name dodo-cluster --image kindest/node:v1.29.2
kubectl apply -f https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.26.0/controller.yaml
kubectl apply -f https://github.com/kyverno/kyverno/releases/download/v1.12.0/install.yaml
istioctl install --set profile=demo -y

# Task 1
kubectl apply -f task1-hardening/k8s/base/
kubectl apply -f task1-hardening/k8s/policies/

# Task 3
kubectl label namespace payments istio-injection=enabled
kubectl apply -f task3-mesh/istio/
kubectl apply -f task3-mesh/networkpolicy/
```
```
