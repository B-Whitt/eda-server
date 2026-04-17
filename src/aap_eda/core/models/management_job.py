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

import uuid

from django.conf import settings
from django.db import models

from aap_eda.core.enums import ExecutionStatus, ManagementJobType

from .base import BaseOrgModel, UniqueNamedModel

__all__ = (
    "ManagementJob",
    "ManagementJobSchedule",
    "ManagementJobExecution",
)


class ManagementJob(BaseOrgModel, UniqueNamedModel):
    """A system-defined management job type with configurable parameters."""

    router_basename = "managementjob"

    class Meta:
        db_table = "core_management_job"
        indexes = [
            models.Index(fields=["job_type"], name="ix_management_job_type"),
        ]
        ordering = ("name",)
        default_permissions = ("view", "change")

    description = models.TextField(default="", blank=True)
    job_type = models.TextField(
        choices=ManagementJobType.choices(),
        null=False,
    )
    is_enabled = models.BooleanField(default=True)
    parameters = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=False)
    modified_at = models.DateTimeField(auto_now=True, null=False)

    def __str__(self):
        return f"{self.name} ({self.job_type})"


class ManagementJobSchedule(models.Model):
    """Cron-based schedule for a management job."""

    class Meta:
        db_table = "core_management_job_schedule"
        ordering = ("management_job__name",)

    management_job = models.OneToOneField(
        ManagementJob,
        on_delete=models.CASCADE,
        related_name="schedule",
    )
    schedule = models.TextField(
        help_text="Cron expression (e.g., '0 2 * * *' for daily at 2 AM)",
    )
    next_run_at = models.DateTimeField(null=True, blank=True)
    last_run_at = models.DateTimeField(null=True, blank=True)
    is_enabled = models.BooleanField(default=True)

    def __str__(self):
        return f"Schedule for {self.management_job.name}: {self.schedule}"


class ManagementJobExecution(BaseOrgModel):
    """Record of a single management job execution."""

    router_basename = "managementjobexecution"

    class Meta:
        db_table = "core_management_job_execution"
        indexes = [
            models.Index(
                fields=["started_at"],
                name="ix_mgmt_job_exec_started",
            ),
            models.Index(
                fields=["status"],
                name="ix_mgmt_job_exec_status",
            ),
        ]
        ordering = ("-started_at",)
        default_permissions = ("view",)

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    management_job = models.ForeignKey(
        ManagementJob,
        on_delete=models.CASCADE,
        related_name="executions",
    )
    status = models.TextField(
        choices=ExecutionStatus.choices(),
        default=ExecutionStatus.PENDING,
    )
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    output = models.TextField(default="", blank=True)
    errors = models.TextField(default="", blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="management_job_executions",
        help_text="User who triggered this execution "
        "(null for scheduled runs)",
    )
