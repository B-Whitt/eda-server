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

from django.contrib import admin

from aap_eda.core.models import (
    ManagementJob,
    ManagementJobExecution,
    ManagementJobSchedule,
)


@admin.register(ManagementJob)
class ManagementJobAdmin(admin.ModelAdmin):
    list_display = ("name", "job_type", "is_enabled", "organization")
    list_filter = ("job_type", "is_enabled")
    readonly_fields = ("created_at", "modified_at")


@admin.register(ManagementJobSchedule)
class ManagementJobScheduleAdmin(admin.ModelAdmin):
    list_display = ("management_job", "schedule", "is_enabled", "next_run_at")
    list_filter = ("is_enabled",)


@admin.register(ManagementJobExecution)
class ManagementJobExecutionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "management_job",
        "status",
        "started_at",
        "finished_at",
    )
    list_filter = ("status",)
    readonly_fields = ("id", "started_at", "finished_at")
