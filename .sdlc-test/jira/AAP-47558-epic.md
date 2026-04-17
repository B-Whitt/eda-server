---
key: AAP-47558
type: Epic
status: In Progress
summary: "Investigate - Management Jobs for Event-Driven Ansible"
assignee: Brandon Whittington
reporter: Zack Kayyali
priority: Normal
project: AAP
components:
  - event-driven-ansible
parent: ANSTRAT-1491
sdp: .sdlc-test/handbook/sdp/eda-management-jobs.md
tech_proposal: .sdlc-test/handbook/proposals/eda-management-jobs/management-job-framework.md
children:
  - AAP-46532
  - AAP-47559
  - AAP-49442
  - AAP-50001
  - AAP-50002
  - AAP-50003
---

# Investigate - Management Jobs for Event-Driven Ansible

## Background

EDA currently lacks management job capabilities that exist in other AAP components (e.g., Controller's cleanup jobs, fact cache management). As EDA usage grows, customers need automated maintenance capabilities for:
- Audit rule log cleanup (logs grow unbounded)
- Credential rotation verification
- Activation health checks and auto-recovery
- Database maintenance (stale records, orphaned data)

## User Stories

As an engineer, I want to create a plan for how to enable EDA management jobs in the platform, so customers can use them to better manage their EDA infrastructure.

As an EDA administrator, I want to schedule recurring maintenance tasks so that my EDA deployment stays healthy without manual intervention.

As an EDA operator, I want to view the status and history of management jobs so I can verify maintenance is happening correctly.

## Acceptance Criteria (Current Phase)

- [ ] Management job framework exists in EDA with a pluggable job type system
- [ ] At least one management job type is implemented (audit rule log cleanup)
- [ ] Job execution history is tracked with status, duration, and output
- [ ] API endpoints exist for CRUD operations on management jobs and on-demand execution

## Future Development (Out of Scope)

- [ ] Management jobs can be scheduled (cron-based) and run on-demand
- [ ] Management jobs respect RBAC permissions
- [ ] Unit and integration tests cover the new functionality comprehensively
- [ ] Additional job types (stale activation cleanup, credential rotation check)

## Definition of Done

- SDP approved and merged
- Tech proposal approved and merged
- All current-phase stories implemented with passing tests
- Code reviewed and merged
- API documentation updated
