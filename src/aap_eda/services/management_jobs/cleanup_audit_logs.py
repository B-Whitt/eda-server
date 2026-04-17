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

import logging
from datetime import timedelta

from django.utils import timezone

from aap_eda.core.models import AuditRule

from .base import BaseManagementJob
from .registry import management_job_registry

logger = logging.getLogger(__name__)

DEFAULT_RETENTION_DAYS = 90
DEFAULT_BATCH_SIZE = 1000


class CleanupAuditLogsJob(BaseManagementJob):
    """Delete AuditRule records older than a configurable retention period.

    Cascade deletes remove associated AuditAction and AuditEvent records.
    Uses batch deletion to avoid long-running table locks.
    """

    def execute(self, parameters: dict) -> str:
        retention_days = parameters.get(
            "retention_days", DEFAULT_RETENTION_DAYS
        )
        batch_size = parameters.get("batch_size", DEFAULT_BATCH_SIZE)
        cutoff = timezone.now() - timedelta(days=retention_days)

        total_deleted = 0

        while True:
            # Fetch a batch of PKs to delete
            batch_pks = list(
                AuditRule.objects.filter(fired_at__lt=cutoff).values_list(
                    "pk", flat=True
                )[:batch_size]
            )

            if not batch_pks:
                break

            deleted_count, _ = AuditRule.objects.filter(
                pk__in=batch_pks
            ).delete()
            total_deleted += deleted_count

            logger.info(
                "CleanupAuditLogsJob: deleted batch of %d records "
                "(total so far: %d)",
                deleted_count,
                total_deleted,
            )

        output = (
            f"Deleted {total_deleted} audit rule records "
            f"older than {retention_days} days"
        )
        logger.info("CleanupAuditLogsJob: %s", output)
        return output

    @classmethod
    def default_parameters(cls) -> dict:
        return {
            "retention_days": DEFAULT_RETENTION_DAYS,
            "batch_size": DEFAULT_BATCH_SIZE,
        }


# Auto-register on import
management_job_registry.register("cleanup_audit_logs", CleanupAuditLogsJob)
