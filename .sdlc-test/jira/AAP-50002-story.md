---
key: AAP-50002
type: Story
status: Ready for Dev
summary: "Add REST API endpoints for management jobs"
assignee: Brandon Whittington
reporter: Brandon Whittington
priority: Normal
project: AAP
components:
  - event-driven-ansible
parent: AAP-47558
order: 2
depends_on:
  - AAP-50001
---

# Add REST API endpoints for management jobs

## User Story

As an EDA administrator, I want API endpoints to create, view, update, and delete management job schedules so I can configure automated maintenance for my EDA deployment.

## Supporting Documentation

- [SDP](../../handbook/sdp/eda-management-jobs.md)
- [Tech Proposal](../../handbook/proposals/eda-management-jobs/management-job-framework.md)

## Acceptance Criteria

- [ ] `GET /api/eda/v1/management-jobs/` lists all management job types with their current schedule status
- [ ] `GET /api/eda/v1/management-jobs/{id}/` returns details for a specific management job
- [ ] `PATCH /api/eda/v1/management-jobs/{id}/` updates management job settings (is_enabled, schedule)
- [ ] `POST /api/eda/v1/management-jobs/{id}/launch/` triggers an on-demand execution
- [ ] `GET /api/eda/v1/management-jobs/{id}/executions/` lists execution history with pagination
- [ ] `GET /api/eda/v1/management-jobs/{id}/executions/{exec_id}/` returns execution details including output
- [ ] Serializers validate input fields
- [ ] API tests cover all CRUD operations

## End to End Test

1. Authenticate as an admin user
2. GET /api/eda/v1/management-jobs/ — verify built-in job types are listed
3. PATCH a management job to set a schedule
4. POST launch to trigger an on-demand run
5. GET executions to verify the run is recorded
If the previous steps are possible, then the test succeeds.
