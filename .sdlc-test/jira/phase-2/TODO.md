# Phase 2 — Future Development

Items deferred from the current epic (AAP-47558) to keep scope manageable.

## Stories to Create

- [ ] **Cron-based management job scheduler** — Add `ManagementJobSchedule` model with cron expression support, a scheduler management command that checks for due jobs, concurrent run prevention, and `next_run_at` calculation
- [ ] **RBAC for management jobs** — Enforce role-based access control on all management job endpoints (admin-only for write/launch, configurable read permissions)
- [ ] **Comprehensive integration tests** — End-to-end tests covering full job lifecycle: create, schedule, execute, verify output, check history; include failure scenarios and concurrent execution
- [ ] **Stale activation cleanup job** — New management job type that identifies and cleans up activations stuck in transient states (STARTING, STOPPING) beyond a configurable timeout
- [ ] **Credential rotation verification job** — Management job that checks credential expiration dates and alerts when rotation is needed

## Dependencies

All phase-2 work depends on phase-1 completion:
- AAP-50001 (data models)
- AAP-50002 (API endpoints)
- AAP-50003 (audit log cleanup job — proves the framework works)
