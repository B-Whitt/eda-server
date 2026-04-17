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

from django.db import migrations

BUILTIN_JOBS = [
    {
        "name": "Cleanup Audit Logs",
        "description": (
            "Remove audit rule logs older than the configured "
            "retention period"
        ),
        "job_type": "cleanup_audit_logs",
        "is_enabled": True,
        "parameters": {"retention_days": 90, "batch_size": 1000},
    },
]


def seed_management_jobs(apps, schema_editor):
    management_job_model = apps.get_model("core", "ManagementJob")
    organization_model = apps.get_model("core", "Organization")

    for org in organization_model.objects.all():
        for job_def in BUILTIN_JOBS:
            management_job_model.objects.get_or_create(
                name=job_def["name"],
                organization=org,
                defaults={
                    "description": job_def["description"],
                    "job_type": job_def["job_type"],
                    "is_enabled": job_def["is_enabled"],
                    "parameters": job_def["parameters"],
                },
            )


def remove_management_jobs(apps, schema_editor):
    management_job_model = apps.get_model("core", "ManagementJob")
    for job_def in BUILTIN_JOBS:
        management_job_model.objects.filter(
            name=job_def["name"],
            job_type=job_def["job_type"],
        ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0071_management_jobs"),
    ]

    operations = [
        migrations.RunPython(
            seed_management_jobs,
            reverse_code=remove_management_jobs,
        ),
    ]
