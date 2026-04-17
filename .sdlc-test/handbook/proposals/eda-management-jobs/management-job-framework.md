# Technical Proposal: Management Job Framework

> Status: Approved (mock)
> SDP: [eda-management-jobs.md](../../sdp/eda-management-jobs.md)
> Epic: AAP-47558

## Overview

Implementation plan for the management job framework in EDA. Covers three stories that deliver models, API, and the first concrete job type.

## Implementation Phases

### Phase 1: Data Models (AAP-50001)

**Files to create/modify:**

| File | Action |
|------|--------|
| `src/aap_eda/core/models/management_job.py` | Create — ManagementJob, ManagementJobExecution |
| `src/aap_eda/core/models/__init__.py` | Modify — export new models |
| `src/aap_eda/core/enums.py` | Modify — add ManagementJobType, ExecutionStatus |
| `src/aap_eda/core/migrations/NNNN_management_jobs.py` | Create — auto-generated migration |

**Model conventions (match existing patterns):**
- Inherit `BaseOrgModel` for organization scoping
- Inherit `UniqueNamedModel` for unique name constraint
- Use `auto_now_add=True` / `auto_now=True` for timestamps
- Define `router_basename` for API routing
- Define `Meta.db_table` explicitly
- Use `models.TextChoices` subclass for enums (follow `ActivationStatus` pattern)

**Enum additions to `core/enums.py`:**
```python
class ManagementJobType(models.TextChoices):
    CLEANUP_AUDIT_LOGS = "cleanup_audit_logs"
    CLEANUP_STALE_ACTIVATIONS = "cleanup_stale_activations"

class ExecutionStatus(models.TextChoices):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
```

### Phase 2: API Endpoints (AAP-50002)

**Files to create/modify:**

| File | Action |
|------|--------|
| `src/aap_eda/api/views/management_job.py` | Create — ManagementJobViewSet |
| `src/aap_eda/api/views/__init__.py` | Modify — export new viewset |
| `src/aap_eda/api/serializers/management_job.py` | Create — Read/Update serializers |
| `src/aap_eda/api/serializers/__init__.py` | Modify — export new serializers |
| `src/aap_eda/api/filters/management_job.py` | Create — ManagementJobFilter |
| `src/aap_eda/api/urls.py` | Modify — register route |

**ViewSet conventions (match ActivationViewSet pattern):**
- Use mixins: `ListModelMixin`, `RetrieveModelMixin`, `UpdateModelMixin`
- No `CreateModelMixin` or `DestroyModelMixin` — job types are system-defined
- Custom `@action(detail=True, methods=['post'])` for `launch`
- `@extend_schema` decorators for OpenAPI docs
- `filter_backends` with `DjangoFilterBackend`
- `get_serializer_class()` method for method-based serializer selection

**Serializers (match RulebookSerializer pattern):**
```python
class ManagementJobReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ManagementJob
        fields = ["id", "name", "description", "job_type", "is_enabled",
                  "parameters", "organization_id", "created_at", "modified_at"]
        read_only_fields = ["id", "name", "description", "job_type",
                           "organization_id", "created_at", "modified_at"]

class ManagementJobUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ManagementJob
        fields = ["is_enabled", "parameters"]

class ManagementJobExecutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ManagementJobExecution
        fields = ["id", "status", "started_at", "finished_at",
                  "output", "errors", "created_by"]
        read_only_fields = fields
```

**URL registration (match existing pattern in urls.py):**
```python
router.register("management-jobs", views.ManagementJobViewSet)
```

### Phase 3: Audit Log Cleanup Job (AAP-50003)

**Files to create:**

| File | Action |
|------|--------|
| `src/aap_eda/services/management_jobs/__init__.py` | Create — package |
| `src/aap_eda/services/management_jobs/base.py` | Create — BaseManagementJob ABC |
| `src/aap_eda/services/management_jobs/registry.py` | Create — job type registry |
| `src/aap_eda/services/management_jobs/cleanup_audit_logs.py` | Create — concrete job |
| `src/aap_eda/core/migrations/NNNN_seed_management_jobs.py` | Create — data migration |

**Cleanup logic:**
- Query `AuditRule` where `fired_at < now() - retention_days`
- Batch delete (1000 records per batch) to avoid table locks
- Cascade deletes `AuditAction` and `AuditEvent` relations
- Return summary: `"Deleted {count} audit rule records older than {retention_days} days"`

**Data migration seeds built-in jobs:**
```python
def seed_management_jobs(apps, schema_editor):
    ManagementJob = apps.get_model('core', 'ManagementJob')
    Organization = apps.get_model('core', 'Organization')
    
    for org in Organization.objects.all():
        ManagementJob.objects.get_or_create(
            name="Cleanup Audit Logs",
            organization=org,
            defaults={
                "description": "Remove audit rule logs older than the configured retention period",
                "job_type": "cleanup_audit_logs",
                "is_enabled": True,
                "parameters": {"retention_days": 90},
            }
        )
```

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Large batch deletes slow down DB | Medium | Batch delete with configurable batch size |
| Cascade deletes on AuditAction/AuditEvent | Low | Already CASCADE in schema; tested |
| Job runs during peak usage | Low | Phase 2 adds scheduling to control timing |

## Estimated Effort

| Story | Estimate |
|-------|----------|
| AAP-50001 (models) | 1 day |
| AAP-50002 (API) | 1-2 days |
| AAP-50003 (cleanup job) | 1 day |
| **Total** | **3-4 days** |
