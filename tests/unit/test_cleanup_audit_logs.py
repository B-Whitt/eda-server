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

from datetime import timedelta

import pytest
from django.utils import timezone

from aap_eda.core import models
from aap_eda.services.management_jobs import (
    CleanupAuditLogsJob,
    management_job_registry,
)


@pytest.fixture
def default_organization():
    return models.Organization.objects.get_or_create(
        name="Default",
        defaults={"description": "Default organization"},
    )[0]


@pytest.fixture
def audit_rules_mixed_ages(default_organization):
    """Create audit rules at various ages: 30, 60, 90, 120, 150 days old."""
    now = timezone.now()
    rules = []
    for days_ago in [30, 60, 90, 120, 150]:
        for i in range(5):
            rule = models.AuditRule.objects.create(
                name=f"rule-{days_ago}d-{i}",
                status="successful",
                fired_at=now - timedelta(days=days_ago),
                organization=default_organization,
            )
            rules.append(rule)
    return rules


# -----------------------------------------------------------------
# Registry tests
# -----------------------------------------------------------------
class TestRegistry:
    def test_cleanup_audit_logs_is_registered(self):
        assert management_job_registry.is_registered("cleanup_audit_logs")

    def test_get_returns_correct_class(self):
        job_class = management_job_registry.get("cleanup_audit_logs")
        assert job_class is CleanupAuditLogsJob

    def test_get_unknown_type_raises(self):
        with pytest.raises(ValueError, match="Unknown management job type"):
            management_job_registry.get("nonexistent_job")


# -----------------------------------------------------------------
# Default parameters
# -----------------------------------------------------------------
class TestDefaultParameters:
    def test_default_parameters(self):
        params = CleanupAuditLogsJob.default_parameters()
        assert params["retention_days"] == 90
        assert params["batch_size"] == 1000


# -----------------------------------------------------------------
# Deletion logic
# -----------------------------------------------------------------
@pytest.mark.django_db
class TestCleanupAuditLogsExecution:
    def test_deletes_records_older_than_retention(
        self, audit_rules_mixed_ages
    ):
        # 25 total: 5 each at 30, 60, 90, 120, 150 days
        job = CleanupAuditLogsJob()
        output = job.execute({"retention_days": 90})

        # Should delete records at 120 and 150 days (10 records)
        # Records at exactly 90 days should NOT be deleted (fired_at < cutoff)
        remaining = models.AuditRule.objects.count()
        assert remaining == 15  # 30d + 60d + 90d remain
        assert "10 audit rule records" in output
        assert "90 days" in output

    def test_deletes_all_with_short_retention(self, audit_rules_mixed_ages):
        job = CleanupAuditLogsJob()
        output = job.execute({"retention_days": 1})

        # All 25 records are older than 1 day
        remaining = models.AuditRule.objects.count()
        assert remaining == 0
        assert "25 audit rule records" in output

    def test_no_records_to_delete(self, audit_rules_mixed_ages):
        job = CleanupAuditLogsJob()
        output = job.execute({"retention_days": 365})

        # Nothing older than 365 days
        remaining = models.AuditRule.objects.count()
        assert remaining == 25
        assert "0 audit rule records" in output

    def test_empty_database(self):
        job = CleanupAuditLogsJob()
        output = job.execute({"retention_days": 90})

        assert "0 audit rule records" in output

    def test_uses_default_retention_when_not_specified(
        self, audit_rules_mixed_ages
    ):
        job = CleanupAuditLogsJob()
        output = job.execute({})  # No retention_days key

        # Default is 90 days — should delete 120d and 150d records
        remaining = models.AuditRule.objects.count()
        assert remaining == 15
        assert "90 days" in output

    def test_batch_deletion_with_small_batch_size(
        self, audit_rules_mixed_ages
    ):
        job = CleanupAuditLogsJob()
        # Use batch_size=3 so it takes multiple passes to delete 10 records
        output = job.execute({"retention_days": 90, "batch_size": 3})

        remaining = models.AuditRule.objects.count()
        assert remaining == 15
        assert "10 audit rule records" in output

    def test_cascade_deletes_audit_actions(self, default_organization):
        import uuid

        now = timezone.now()
        old_rule = models.AuditRule.objects.create(
            name="old-rule",
            status="successful",
            fired_at=now - timedelta(days=120),
            organization=default_organization,
        )
        models.AuditAction.objects.create(
            id=uuid.uuid4(),
            name="debug",
            audit_rule=old_rule,
            status="successful",
            fired_at=now - timedelta(days=120),
        )

        assert models.AuditAction.objects.count() == 1

        job = CleanupAuditLogsJob()
        job.execute({"retention_days": 90})

        assert models.AuditRule.objects.count() == 0
        assert models.AuditAction.objects.count() == 0  # cascade
