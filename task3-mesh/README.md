```markdown
# Task 3 — Service Mesh & Zero-Trust (Istio)

## Architecture
```
[Client] → [Istio Ingress Gateway] → [ledger-api] ←mTLS→ [audit-logger]
                                           ↑
                         AuthorizationPolicy (SPIFFE identity-based)
                                           ↑
                              NetworkPolicy (defence-in-depth)
```

## What Was Implemented

### 1. Istio Installation
- Profile: `demo`
- Version: `1.21.0`
- Components: istiod, ingress gateway, egress gateway

### 2. mTLS STRICT Enforcement
- `PeerAuthentication` → `STRICT` mode on `payments` namespace
- All plaintext connections refused
- **Proof:** Non-mesh pod curl attempt → `exit code 56` (connection reset)

### 3. AuthorizationPolicy (Default Deny)
- `default-deny-all` → denies all traffic in payments namespace
- `allow-audit-logger-to-ledger` → SPIFFE identity-based allow
- `allow-ingress-to-ledger` → ingress gateway allow
- Identity: `cluster.local/ns/payments/sa/ledger-api-sa`

### 4. NetworkPolicy (Defence-in-Depth)
- `default-deny-all` → blocks all ingress/egress at node level
- `allow-ledger-api-ingress` → allows only from istio-system + audit-logger
- `allow-ledger-api-egress-dns` → allows only DNS (port 53)

### 5. Istio Sidecar Injection
- Namespace label: `istio-injection=enabled`
- Pods show `2/2` (app + istio-proxy sidecar)

## Workload Certificate Issuance & Rotation
- **Issuer:** Istio CA (istiod)
- **Standard:** SPIFFE X.509 certificates
- **Identity format:** `spiffe://cluster.local/ns/payments/sa/ledger-api-sa`
- **Rotation:** Every 24 hours (default) — automatic, zero downtime
- **Trust root:** Istio self-signed CA (pluggable with external CA like Vault)

## Defence-in-Depth — Two Layers

| Layer | What it catches |
|-------|----------------|
| **NetworkPolicy** | Node-level traffic — blocks even if Istio sidecar missing |
| **Istio mTLS** | Encrypted + mutually authenticated service-to-service |
| **AuthorizationPolicy** | Identity-based allow/deny beyond just encryption |

NetworkPolicy catches what Istio misses (no sidecar scenarios).
Istio catches what NetworkPolicy misses (identity-based authz, encryption).

## PCI DSS Relevance
- mTLS satisfies PCI DSS Req 4.2.1 (encrypt cardholder data in transit)
- AuthorizationPolicy satisfies Req 7 (restrict access by business need)
- NetworkPolicy satisfies Req 1 (install and maintain network security controls)

## Proof Screenshots

| Screenshot | Description |
|-----------|-------------|
| `docs/istio-pods.png` | Istio system pods running |
| `docs/mtls-strict.png` | PeerAuthentication STRICT mode |
| `docs/authz-policies.png` | AuthorizationPolicies applied |
| `docs/network-policies.png` | NetworkPolicies applied |
| `docs/sidecar-inject.png` | Pod showing 2/2 (app + sidecar) |
| `docs/mtls-block-proof.png` | Non-mesh curl → exit code 56 (blocked!) |
| `docs/mtls-tls-check.png` | mTLS mode verification |

## How to Run
```bash
# Install Istio
istioctl install --set profile=demo -y

# Enable injection
kubectl label namespace payments istio-injection=enabled

# Apply policies
kubectl apply -f istio/peer-authentication.yaml
kubectl apply -f istio/authorization-policy.yaml
kubectl apply -f networkpolicy/default-deny.yaml

# Verify
kubectl get pods -n payments        # Should show 2/2
kubectl get peerauthentication -n payments
kubectl get authorizationpolicy -n payments

# Test mTLS block
kubectl run curl-test --image=curlimages/curl:8.5.0 \
  --restart=Never --namespace=default -- sleep 3600
kubectl exec curl-test -n default -- \
  curl -s http://audit-logger.payments.svc.cluster.local:9000 --max-time 5
# Expected: exit code 56 (connection reset — mTLS blocking plaintext!)
```
```