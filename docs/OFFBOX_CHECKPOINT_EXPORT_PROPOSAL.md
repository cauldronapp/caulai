# CAUL AI — Off-Box Audit Checkpoint Export PROPOSAL (NOT ACTIVATED)

**Status:** PROPOSAL ONLY. Awaiting separate written approval. No external service is
provisioned, connected, or contacted. No credentials requested. $0 to date.

Purpose: after final Phase 1A acceptance, periodically export independent audit-chain
checkpoints `(chain_env, chain_org, seq, head_hash, event_count, timestamp)` to an
off-box location so a DB-owner compromise (the documented residual risk) can be detected
by comparing on-box state against a previously exported, write-restricted checkpoint.

## Options (choose one at approval time)
### Option A — Cauldron-owned Git repository (recommended, $0)
- **Destination & ownership:** a dedicated **private** `caul-audit-checkpoints` repo under the
  Cauldron Technologies, Inc. GitHub org. Fully owned/controlled by Cauldron.
- **What is exported:** ONLY checkpoint tuples + chain metadata (no event payloads, no PII,
  no secrets). Append-only JSONL, one line per checkpoint.
- **Security & access controls:** private repo; branch protection; least-privilege
  machine user or fine-grained PAT limited to that single repo; commits signed.
- **Credentials required:** one fine-grained GitHub token (write to the one repo only),
  stored as `AUDIT_EXPORT_TOKEN` in backend secrets — never in code/`crons.yml`/frontend.
- **Retention & recovery:** full Git history = immutable-by-convention retention; recovery
  = clone repo and diff exported head hash vs live `verify_chain` output.
- **Cost:** **$0** on GitHub Free/Team for a private repo of small text files. Truly $0.
- **Failure behavior:** export failures are logged and retried next cycle; on-box
  verification is unaffected. Non-blocking.
- **Revocation:** revoke the fine-grained token; delete the secret. Export stops immediately;
  no other system access is possible with that token.

### Option B — Cauldron-controlled object storage (S3/GCS)
- **Destination & ownership:** a Cauldron-owned bucket with Object Lock (WORM) enabled.
- **Security:** bucket policy denies delete/overwrite (compliance lock); SSE encryption;
  IAM role scoped to `PutObject` on one prefix only.
- **Credentials:** one scoped IAM key (`AUDIT_EXPORT_*`) in backend secrets.
- **Retention & recovery:** Object Lock retention window (e.g., 1 year); recovery via read of
  the locked object.
- **Cost:** small but **NOT strictly $0** (storage + request pennies/month). Flag before use.
- **Failure/revocation:** failures logged + retried; revoke by disabling the IAM key.

## Common controls (both options)
- Export contains **no** event payloads, **no** PII, **no** secrets — only hashes/metadata.
- Transport over TLS; least-privilege single-purpose credential; audit every export attempt
  into the on-box audit chain (`audit.export.checkpoint`).
- Idempotent: re-exporting an already-exported seq is a no-op.

## Explicit non-actions (binding)
- Nothing is provisioned or connected now. No account created, no token requested, no bucket made.
- Activation requires separate written approval and (for Option B) an itemized cost approval.
- Until then, scheduled verification writes checkpoints **on-box only** (local dev + staging).
