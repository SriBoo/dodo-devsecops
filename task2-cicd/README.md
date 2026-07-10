```markdown
# Task 2 — Secure CI/CD Pipeline & Supply Chain

## Overview
Rebuilt the delivery path with security enforced at every stage.
Pipeline: Secrets Scan → SAST → CVE Scan → Build → Image Scan → Sign → Deploy

## Pipeline Architecture

```
Push to main
    ↓
┌─────────────────────────────────────┐
│  Stage 1: Secrets Scan (Gitleaks)   │ ← Hard block on any secret
│  Stage 2: SAST (Semgrep)            │ ← OWASP Top 10, Python rules
│  Stage 3: Dependency CVE (Trivy)    │ ← CRITICAL/HIGH CVEs flagged
└─────────────────────────────────────┘
    ↓
┌─────────────────────────┐
│  Stage 4: Build Image   │ ← docker build + push to GHCR
└─────────────────────────┘
    ↓
┌──────────────────────────────────────┐
│  Stage 5: Image CVE Scan (Trivy)     │ ← Scan built image
│  Stage 6: Sign (Cosign keyless)      │ ← OIDC-based signing
└──────────────────────────────────────┘
```

## Security Gates

| Gate | Tool | Policy |
|------|------|--------|
| Secrets scan | Gitleaks | Hard block — any secret found |
| SAST | Semgrep | Warn — OWASP Top 10, Python, secrets ruleset |
| Dependency CVE | Trivy (fs) | Warn — CRITICAL/HIGH flagged |
| Image CVE | Trivy (image) | Warn — CRITICAL flagged |
| Image signing | Cosign keyless | OIDC-based signing via GitHub Actions |

## CVE With No Fix Policy
If a CRITICAL CVE has no upstream fix:
1. Document in `docs/cve-exceptions.md` with justification
2. Use `--ignore-unfixed` flag temporarily
3. Track for upstream fix — re-evaluate within 30 days
4. Apply Kyverno policy to block specific vulnerable digest

## Security Fixes Applied to app.py

| Issue | Fix |
|-------|-----|
| YAML injection | `yaml.safe_load()` instead of `yaml.load()` |
| SSRF | URL allowlist — only internal services allowed |
| PAN data exposure | Masked PANs in LEDGER (`424242******4242`) |
| Outdated deps | Updated all packages to latest stable versions |

## Dockerfile Hardening
- Base image: `python:3.11-slim` (was `python:3.6-slim` — EOL)
- Multi-stage build — minimal final image
- Non-root user (`appuser`, UID 1000)
- No secrets in image layers

## Pipeline Results

| Stage | Status | Notes |
|-------|--------|-------|
| Secrets Scan — Gitleaks | ✅ Pass | No leaks detected |
| SAST — Semgrep | ✅ Pass | Rules applied |
| Dependency CVE — Trivy | ✅ Pass | CVEs logged |
| Build Image | ✅ Pass | Pushed to GHCR |
| Image CVE — Trivy | ✅ Pass | Scanned |
| Sign — Cosign | ⚠️ Note | See below |

## Note on Cosign Signing
Cosign keyless signing uses GitHub OIDC token for workload identity.
The sign step encounters OIDC configuration limitations on this account.
The architecture is correctly implemented and would work with proper
GitHub Actions OIDC permissions configured at organization level.

## GitOps — ArgoCD (Architecture)
ArgoCD would watch `task1-hardening/k8s/` folder as source of truth.
- Any manual `kubectl edit` → ArgoCD detects drift → auto-reverts within 3 mins
- Sync policy: `automated` with `selfHeal: true`
- Not deployed locally due to time constraints — would implement in production

## SLSA Attestation
Cosign attest command is implemented in the pipeline:
```yaml
cosign attest --yes \
  --predicate <(echo '{"buildType":"github-actions",...}') \
  --type slsaprovenance \
  $IMAGE@$DIGEST
```
Requires same OIDC token as signing — would work with org-level OIDC permissions.

## Screenshots
| File | Description |
|------|-------------|
| `docs/pipeline-runs.png` | All pipeline runs history |
| `docs/pipeline-summary.png` | 5 stages green + No leaks detected |
| `docs/ghcr-image.png` | ledger-api package published to GHCR |

## Pipeline Run
[GitHub Actions](https://github.com/SriBoo/dodo-devsecops/actions)

## How to Run Locally
```bash
# Build
docker build -t ledger-api:local ./ledger-api-src/app

# Scan
trivy image ledger-api:local

# Sign (requires cosign + OIDC)
cosign sign --yes ghcr.io/SriBoo/dodo-devsecops/ledger-api@sha256:ACTUAL_DIGEST
```
```