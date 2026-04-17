---
key: AAP-50001
type: Story
status: Ready for Dev
summary: "Add management job data models and database migrations"
assignee: Brandon Whittington
reporter: Brandon Whittington
priority: Normal
project: AAP
components:
  - event-driven-ansible
parent: AAP-47558
order: 1
---

# Add management job data models and database migrations

## User Story

As an EDA developer, I want data models for management jobs so that the system can persist job definitions, schedules, and execution history.

## Supporting Documentation

- [SDP](../../handbook/sdp/eda-management-jobs.md)
- [Tech Proposal](../../handbook/proposals/eda-management-jobs/management-job-framework.md)

## Acceptance Criteria

- [ ] `ManagementJob` model exists with fields: name, description, job_type (enum), is_enabled (bool), created_at, modified_at
- [ ] `ManagementJobSchedule` model exists with fields: management_job (FK), schedule (cron string), next_run_at, last_run_at, is_enabled
- [ ] `ManagementJobExecution` model exists with fields: management_job (FK), status (enum: pending/running/completed/failed), started_at, finished_at, output (text), errors (text)
- [ ] Job type enum includes at least: `cleanup_audit_logs`, `cleanup_stale_activations`
- [ ] Database migration is generated and applies cleanly
- [ ] Models are registered in Django admin
- [ ] Unit tests verify model creation, relationships, and constraints

## End to End Test

1. Apply the migration to a clean database
2. Create a ManagementJob instance via Django ORM
3. Create a ManagementJobSchedule linked to the job
4. Create a ManagementJobExecution linked to the job
5. Verify all relationships and constraints work

If the previous steps are possible, then the test succeeds.
