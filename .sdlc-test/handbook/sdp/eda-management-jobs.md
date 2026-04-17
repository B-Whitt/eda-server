# System Design Plan: Management Jobs for Event-Driven Ansible

> Status: Approved (mock)
> Author: Brandon Whittington
> Epic: AAP-47558
> Feature: ANSTRAT-1491

## Overview

Add a management job framework to EDA that enables automated maintenance tasks. The framework is pluggable — new job types can be added by implementing a base class. Phase 1 delivers the framework plus one concrete job type (audit rule log cleanup).

## Problem Statement

EDA lacks automated maintenance capabilities. Audit rule logs grow unbounded, consuming database storage. Operators must manually manage cleanup. AAP Controller has management jobs (cleanup_jobs, cleanup_tokens, etc.) — EDA needs the equivalent.

## Architecture

### Component Design

```
src/aap_eda/
├── core/
│   ├── models/
│   │   └── management_job.py      # ManagementJob, ManagementJobExecution
│   └── enums.py                    # ManagementJobType, ExecutionStatus (additions)
├── api/
│   ├── views/
│   │   └── management_job.py      # ManagementJobViewSet
│   ├── serializers/
│   │   └── management_job.py      # Read/Create/Update serializers
│   └── filters/
│       └── management_job.py      # ManagementJobFilter
├── services/
│   └── management_jobs/
│       ├── __init__.py
│       ├── base.py                # BaseManagementJob abstract class
│       ├── registry.py            # Job type registry
│       └── cleanup_audit_logs.py  # First concrete job type
└── urls.py                        # Add management-jobs route
```

### Data Models

#### ManagementJob

| Field | Type | Notes |
|-------|------|-------|
| id | AutoField | PK |
| name | TextField | Unique per org |
| description | TextField | Human-readable description |
| job_type | TextField | Enum: ManagementJobType choices |
| is_enabled | BooleanField | Default True |
| parameters | JSONField | Job-specific config (e.g., retention_days) |
| organization | ForeignKey | BaseOrgModel |
| created_at | DateTimeField | auto_now_add |
| modified_at | DateTimeField | auto_now |

Inherits: `BaseOrgModel`, `UniqueNamedModel`

#### ManagementJobExecution

| Field | Type | Notes |
|-------|------|-------|
| id | UUIDField | PK, auto-generated |
| management_job | ForeignKey | CASCADE to ManagementJob |
| status | TextField | Enum: pending/running/completed/failed |
| started_at | DateTimeField | Nullable |
| finished_at | DateTimeField | Nullable |
| output | TextField | Job output log |
| errors | TextField | Error details if failed |
| created_by | ForeignKey | User who triggered (null for scheduled) |

Inherits: `BaseOrgModel`

### API Contracts

```
GET    /api/eda/v1/management-jobs/                    # List all job types
GET    /api/eda/v1/management-jobs/{id}/                # Job detail
PATCH  /api/eda/v1/management-jobs/{id}/                # Update settings (is_enabled, parameters)
POST   /api/eda/v1/management-jobs/{id}/launch/         # Trigger on-demand execution
GET    /api/eda/v1/management-jobs/{id}/executions/      # List execution history
GET    /api/eda/v1/management-jobs/{id}/executions/{eid}/ # Execution detail
```

### Job Framework Design

```python
# Base class pattern
class BaseManagementJob(ABC):
    """Abstract base for management job implementations."""
    
    @abstractmethod
    def execute(self, parameters: dict) -> str:
        """Run the job. Returns output string. Raises on failure."""
        ...
    
    @classmethod
    @abstractmethod
    def default_parameters(cls) -> dict:
        """Default parameters for this job type."""
        ...

# Registry pattern
class ManagementJobRegistry:
    _registry: dict[str, type[BaseManagementJob]] = {}
    
    @classmethod
    def register(cls, job_type: str, job_class: type[BaseManagementJob]):
        cls._registry[job_type] = job_class
    
    @classmethod
    def get(cls, job_type: str) -> type[BaseManagementJob]:
        return cls._registry[job_type]
```

### Migration Plan

1. Create migration for ManagementJob and ManagementJobExecution models
2. Data migration to seed built-in job types (cleanup_audit_logs)
3. No schema changes to existing tables

## Test Strategy

- Unit tests: model creation, registry, job execution logic
- Integration tests: API endpoint CRUD, launch action, execution history
- Follow existing patterns in `tests/integration/api/` and `tests/unit/`

## Cross-Service Dependencies

- None. Management jobs are internal to EDA.
- Future: may integrate with AAP Controller's unified management job view.

## Open Questions (Resolved)

1. ~~Should jobs run in-process or via Celery?~~ → In-process for phase 1 (synchronous on launch). Celery integration in phase 2.
2. ~~Shared job types across AAP components?~~ → Deferred. EDA-specific for now.
