#  Copyright 2024 Red Hat, Inc.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import pytest
from django.db import IntegrityError

from aap_eda.core import models
from aap_eda.core.enums import ExecutionStatus, ManagementJobType


@pytest.fixture
def default_organization():
    return models.Organization.objects.get_or_create(
        name="Default",
        defaults={"description": "Default organization"},
    )[0]


@pytest.fixture
def management_job(default_organization):
    return models.ManagementJob.objects.create(
        name="Cleanup Audit Logs",
        description="Remove old audit rule logs",
        job_type=ManagementJobType.CLEANUP_AUDIT_LOGS,
        is_enabled=True,
        parameters={"retention_days": 90},
        organization=default_organization,
    )


# -----------------------------------------------------------------
# ManagementJob model tests
# -----------------------------------------------------------------
@pytest.mark.django_db
class TestManagementJobModel:
    def test_create_management_job(self, management_job):
        assert management_job.pk is not None
        assert management_job.name == "Cleanup Audit Logs"
        assert management_job.job_type == ManagementJobType.CLEANUP_AUDIT_LOGS
        assert management_job.is_enabled is True
        assert management_job.parameters == {"retention_days": 90}
        assert management_job.created_at is not None
        assert management_job.modified_at is not None

    def test_str_representation(self, management_job):
        assert str(management_job) == "Cleanup Audit Logs (cleanup_audit_logs)"

    def test_unique_name_constraint(
        self, management_job, default_organization
    ):
        with pytest.raises(IntegrityError):
            models.ManagementJob.objects.create(
                name="Cleanup Audit Logs",
                job_type=ManagementJobType.CLEANUP_STALE_ACTIVATIONS,
                organization=default_organization,
            )

    def test_default_values(self, default_organization):
        job = models.ManagementJob.objects.create(
            name="Minimal Job",
            job_type=ManagementJobType.CLEANUP_STALE_ACTIVATIONS,
            organization=default_organization,
        )
        assert job.is_enabled is True
        assert job.description == ""
        assert job.parameters == {}

    def test_organization_cascade_delete(self, default_organization):
        job = models.ManagementJob.objects.create(
            name="Temp Job",
            job_type=ManagementJobType.CLEANUP_AUDIT_LOGS,
            organization=default_organization,
        )
        job_id = job.pk
        default_organization.delete()
        assert not models.ManagementJob.objects.filter(pk=job_id).exists()


# -----------------------------------------------------------------
# ManagementJobSchedule model tests
# -----------------------------------------------------------------
@pytest.mark.django_db
class TestManagementJobScheduleModel:
    def test_create_schedule(self, management_job):
        schedule = models.ManagementJobSchedule.objects.create(
            management_job=management_job,
            schedule="0 2 * * *",
            is_enabled=True,
        )
        assert schedule.pk is not None
        assert schedule.schedule == "0 2 * * *"
        assert schedule.is_enabled is True
        assert schedule.next_run_at is None
        assert schedule.last_run_at is None

    def test_str_representation(self, management_job):
        schedule = models.ManagementJobSchedule.objects.create(
            management_job=management_job,
            schedule="*/5 * * * *",
        )
        assert "Cleanup Audit Logs" in str(schedule)
        assert "*/5 * * * *" in str(schedule)

    def test_one_to_one_constraint(self, management_job):
        models.ManagementJobSchedule.objects.create(
            management_job=management_job,
            schedule="0 2 * * *",
        )
        with pytest.raises(IntegrityError):
            models.ManagementJobSchedule.objects.create(
                management_job=management_job,
                schedule="0 3 * * *",
            )

    def test_cascade_delete_with_job(self, management_job):
        schedule = models.ManagementJobSchedule.objects.create(
            management_job=management_job,
            schedule="0 2 * * *",
        )
        schedule_id = schedule.pk
        management_job.delete()
        assert not models.ManagementJobSchedule.objects.filter(
            pk=schedule_id
        ).exists()

    def test_reverse_relation(self, management_job):
        models.ManagementJobSchedule.objects.create(
            management_job=management_job,
            schedule="0 2 * * *",
        )
        assert management_job.schedule.schedule == "0 2 * * *"


# -----------------------------------------------------------------
# ManagementJobExecution model tests
# -----------------------------------------------------------------
@pytest.mark.django_db
class TestManagementJobExecutionModel:
    def test_create_execution(self, management_job):
        execution = models.ManagementJobExecution.objects.create(
            management_job=management_job,
            status=ExecutionStatus.PENDING,
            organization=management_job.organization,
        )
        assert execution.pk is not None
        assert execution.status == ExecutionStatus.PENDING
        assert execution.started_at is None
        assert execution.finished_at is None
        assert execution.output == ""
        assert execution.errors == ""
        assert execution.created_by is None

    def test_uuid_primary_key(self, management_job):
        execution = models.ManagementJobExecution.objects.create(
            management_job=management_job,
            status=ExecutionStatus.PENDING,
            organization=management_job.organization,
        )
        # UUID is 36 chars with hyphens
        assert len(str(execution.pk)) == 36

    def test_execution_with_output(self, management_job):
        from django.utils import timezone

        now = timezone.now()
        execution = models.ManagementJobExecution.objects.create(
            management_job=management_job,
            status=ExecutionStatus.COMPLETED,
            started_at=now,
            finished_at=now,
            output="Deleted 42 audit rule records older than 90 days",
            organization=management_job.organization,
        )
        assert execution.status == ExecutionStatus.COMPLETED
        assert "42 audit rule records" in execution.output

    def test_execution_with_errors(self, management_job):
        execution = models.ManagementJobExecution.objects.create(
            management_job=management_job,
            status=ExecutionStatus.FAILED,
            errors="Database connection timeout",
            organization=management_job.organization,
        )
        assert execution.status == ExecutionStatus.FAILED
        assert execution.errors == "Database connection timeout"

    def test_multiple_executions_per_job(self, management_job):
        for _i in range(3):
            models.ManagementJobExecution.objects.create(
                management_job=management_job,
                status=ExecutionStatus.COMPLETED,
                organization=management_job.organization,
            )
        assert management_job.executions.count() == 3

    def test_cascade_delete_with_job(self, management_job):
        execution = models.ManagementJobExecution.objects.create(
            management_job=management_job,
            status=ExecutionStatus.COMPLETED,
            organization=management_job.organization,
        )
        exec_id = execution.pk
        management_job.delete()
        assert not models.ManagementJobExecution.objects.filter(
            pk=exec_id
        ).exists()

    def test_created_by_set_null_on_user_delete(self, management_job):
        user = models.User.objects.create_user(
            username="test_operator",
            password="secret",
        )
        execution = models.ManagementJobExecution.objects.create(
            management_job=management_job,
            status=ExecutionStatus.COMPLETED,
            created_by=user,
            organization=management_job.organization,
        )
        user.delete()
        execution.refresh_from_db()
        assert execution.created_by is None


# -----------------------------------------------------------------
# Enum tests
# -----------------------------------------------------------------
class TestEnums:
    def test_management_job_type_values(self):
        assert ManagementJobType.CLEANUP_AUDIT_LOGS == "cleanup_audit_logs"
        assert (
            ManagementJobType.CLEANUP_STALE_ACTIVATIONS
            == "cleanup_stale_activations"
        )

    def test_management_job_type_choices(self):
        choices = ManagementJobType.choices()
        assert ("cleanup_audit_logs", "cleanup_audit_logs") in choices
        assert (
            "cleanup_stale_activations",
            "cleanup_stale_activations",
        ) in choices

    def test_execution_status_values(self):
        assert ExecutionStatus.PENDING == "pending"
        assert ExecutionStatus.RUNNING == "running"
        assert ExecutionStatus.COMPLETED == "completed"
        assert ExecutionStatus.FAILED == "failed"

    def test_execution_status_choices(self):
        choices = ExecutionStatus.choices()
        assert len(choices) == 4
