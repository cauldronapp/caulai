# CAUL AI — Backup, Restore & Export (Phase 1A)

PostgreSQL is the authoritative system of record. All data remains owned/controllable
by Cauldron Technologies, Inc. and is fully exportable.

## Backup (dev)
```
PGPASSWORD=<owner_pw> pg_dump -h localhost -U postgres -d caul_dev -F c -f caul_dev_backup.dump
```

## Backup (staging)
```
PGPASSWORD=<owner_pw> pg_dump -h localhost -U postgres -d caul_staging -F c -f caul_staging_backup.dump
```

## Restore (proven)
```
PGPASSWORD=<owner_pw> psql  -h localhost -U postgres -c "CREATE DATABASE caul_restore_test;"
PGPASSWORD=<owner_pw> pg_restore -h localhost -U postgres -d caul_restore_test --no-owner caul_dev_backup.dump
```

## Verified restore evidence (Phase 1A foundation)
A dev backup (`52K`, custom format) was restored into a scratch database and verified:
`users`, `audit_events`, and `permissions` tables restored with their row counts intact.
The scratch database was then dropped. This proves backup + at least one restore.

## Export
- Full DB: `pg_dump` (above).
- Audit log (portable): `GET /api/audit/export?fmt=csv` (requires `audit:export`).

## Notes
- The local cluster data directory is persisted at `/app/postgres_data`.
- Dev and staging are physically separate databases with separate credentials.
- True separate-SERVER isolation is deferred to a future provisioning approval (see PREFLIGHT_REPORT.md).
