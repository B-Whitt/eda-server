---
key: AAP-50003
type: Story
status: Ready for Dev
summary: "Implement audit rule log cleanup management job"
assignee: Brandon Whittington
reporter: Brandon Whittington
priority: Normal
project: AAP
components:
  - event-driven-ansible
parent: AAP-47558
order: 3
depends_on:
  - AAP-50001
  - AAP-50002
---

# Implement audit rule log cleanup management job

## User Story

As an EDA administrator, I want an automated job that cleans up old audit rule logs so that database storage doesn't grow unbounded.

## Supporting Documentation

- [SDP](../../handbook/sdp/eda-management-jobs.md)
- [Tech Proposal](../../handbook/proposals/eda-management-jobs/management-job-framework.md)
- Related: AAP-46532 (spike: give user option to delete audit rule logs)

## Acceptance Criteria

- [ ] A `CleanupAuditLogsJob` class exists implementing the management job interface
- [ ] Job accepts a `retention_days` parameter (default: 90 days)
- [ ] Job deletes `AuditRule` records older than `retention_days`
- [ ] Job logs the number of records deleted in its execution output
- [ ] Job handles empty result sets gracefully (no records to delete)
- [ ] Job uses batch deletion to avoid locking the table for large deletes
- [ ] A database fixture or migration registers this job type as a built-in management job
- [ ] Unit tests verify deletion logic with various retention periods
- [ ] Unit tests verify batch deletion behavior

## End to End Test

1. Create 100 AuditRule records with created_at spanning 30, 60, 90, 120, and 150 days ago
2. Run the cleanup job with retention_days=90
3. Verify only records older than 90 days are deleted
4. Verify execution record shows count of deleted records
5. Run again — verify 0 records deleted, job completes successfully

If the previous steps are possible, then the test succeeds.
