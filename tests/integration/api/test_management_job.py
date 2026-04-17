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
from rest_framework import status
from rest_framework.test import APIClient

from aap_eda.core import models
from aap_eda.core.enums import ExecutionStatus, ManagementJobType
from tests.integration.constants import api_url_v1

MANAGEMENT_JOBS_URL = f"{api_url_v1}/management-jobs"


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


@pytest.fixture
def disabled_management_job(default_organization):
    return models.ManagementJob.objects.create(
        name="Cleanup Stale Activations",
        description="Remove stale activations",
        job_type=ManagementJobType.CLEANUP_STALE_ACTIVATIONS,
        is_enabled=False,
        parameters={},
        organization=default_organization,
    )


@pytest.fixture
def management_job_execution(management_job):
    return models.ManagementJobExecution.objects.create(
        management_job=management_job,
        status=ExecutionStatus.COMPLETED,
        output="Deleted 42 audit rule records older than 90 days",
        organization=management_job.organization,
    )


# -----------------------------------------------------------------
# List management jobs
# -----------------------------------------------------------------
@pytest.mark.django_db
def test_list_management_jobs(
    management_job: models.ManagementJob,
    admin_client: APIClient,
):
    response = admin_client.get(f"{MANAGEMENT_JOBS_URL}/")
    assert response.status_code == status.HTTP_200_OK
    results = response.data["results"]
    assert len(results) >= 1
    job = next(r for r in results if r["id"] == management_job.id)
    assert job["name"] == "Cleanup Audit Logs"
    assert job["job_type"] == "cleanup_audit_logs"
    assert job["is_enabled"] is True


@pytest.mark.django_db
def test_list_management_jobs_filter_by_type(
    management_job: models.ManagementJob,
    disabled_management_job: models.ManagementJob,
    admin_client: APIClient,
):
    response = admin_client.get(
        f"{MANAGEMENT_JOBS_URL}/",
        {"job_type": "cleanup_audit_logs"},
    )
    assert response.status_code == status.HTTP_200_OK
    results = response.data["results"]
    assert all(r["job_type"] == "cleanup_audit_logs" for r in results)


@pytest.mark.django_db
def test_list_management_jobs_filter_by_enabled(
    management_job: models.ManagementJob,
    disabled_management_job: models.ManagementJob,
    admin_client: APIClient,
):
    response = admin_client.get(
        f"{MANAGEMENT_JOBS_URL}/",
        {"is_enabled": "true"},
    )
    assert response.status_code == status.HTTP_200_OK
    results = response.data["results"]
    assert all(r["is_enabled"] is True for r in results)


# -----------------------------------------------------------------
# Retrieve management job
# -----------------------------------------------------------------
@pytest.mark.django_db
def test_retrieve_management_job(
    management_job: models.ManagementJob,
    admin_client: APIClient,
):
    response = admin_client.get(f"{MANAGEMENT_JOBS_URL}/{management_job.id}/")
    assert response.status_code == status.HTTP_200_OK
    assert response.data["id"] == management_job.id
    assert response.data["name"] == "Cleanup Audit Logs"
    assert response.data["parameters"] == {"retention_days": 90}


@pytest.mark.django_db
def test_retrieve_management_job_not_found(
    admin_client: APIClient,
):
    response = admin_client.get(f"{MANAGEMENT_JOBS_URL}/99999/")
    assert response.status_code == status.HTTP_404_NOT_FOUND


# -----------------------------------------------------------------
# Update management job
# -----------------------------------------------------------------
@pytest.mark.django_db
def test_partial_update_management_job(
    management_job: models.ManagementJob,
    admin_client: APIClient,
):
    response = admin_client.patch(
        f"{MANAGEMENT_JOBS_URL}/{management_job.id}/",
        data={"is_enabled": False, "parameters": {"retention_days": 30}},
        format="json",
    )
    assert response.status_code == status.HTTP_200_OK
    management_job.refresh_from_db()
    assert management_job.is_enabled is False
    assert management_job.parameters == {"retention_days": 30}


@pytest.mark.django_db
def test_partial_update_only_parameters(
    management_job: models.ManagementJob,
    admin_client: APIClient,
):
    response = admin_client.patch(
        f"{MANAGEMENT_JOBS_URL}/{management_job.id}/",
        data={"parameters": {"retention_days": 7}},
        format="json",
    )
    assert response.status_code == status.HTTP_200_OK
    management_job.refresh_from_db()
    assert management_job.parameters == {"retention_days": 7}
    assert management_job.is_enabled is True  # unchanged


# -----------------------------------------------------------------
# Launch management job
# -----------------------------------------------------------------
@pytest.mark.django_db
def test_launch_management_job(
    management_job: models.ManagementJob,
    admin_client: APIClient,
):
    response = admin_client.post(
        f"{MANAGEMENT_JOBS_URL}/{management_job.id}/launch/"
    )
    assert response.status_code == status.HTTP_202_ACCEPTED
    assert response.data["status"] == "pending"
    assert response.data["management_job_id"] == management_job.id

    # Verify execution was created in DB
    assert models.ManagementJobExecution.objects.filter(
        management_job=management_job,
    ).exists()


@pytest.mark.django_db
def test_launch_disabled_management_job(
    disabled_management_job: models.ManagementJob,
    admin_client: APIClient,
):
    response = admin_client.post(
        f"{MANAGEMENT_JOBS_URL}/{disabled_management_job.id}/launch/"
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "disabled" in response.data["detail"]


# -----------------------------------------------------------------
# List executions
# -----------------------------------------------------------------
@pytest.mark.django_db
def test_list_executions(
    management_job: models.ManagementJob,
    management_job_execution: models.ManagementJobExecution,
    admin_client: APIClient,
):
    response = admin_client.get(
        f"{MANAGEMENT_JOBS_URL}/{management_job.id}/executions/"
    )
    assert response.status_code == status.HTTP_200_OK
    results = response.data["results"]
    assert len(results) == 1
    assert results[0]["status"] == "completed"
    assert "42 audit rule records" in results[0]["output"]


@pytest.mark.django_db
def test_list_executions_empty(
    management_job: models.ManagementJob,
    admin_client: APIClient,
):
    response = admin_client.get(
        f"{MANAGEMENT_JOBS_URL}/{management_job.id}/executions/"
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.data["results"] == []


# -----------------------------------------------------------------
# Retrieve execution detail
# -----------------------------------------------------------------
@pytest.mark.django_db
def test_retrieve_execution_detail(
    management_job: models.ManagementJob,
    management_job_execution: models.ManagementJobExecution,
    admin_client: APIClient,
):
    response = admin_client.get(
        f"{MANAGEMENT_JOBS_URL}/{management_job.id}"
        f"/executions/{management_job_execution.id}/"
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.data["id"] == str(management_job_execution.id)
    assert response.data["status"] == "completed"
    assert response.data["output"] == (
        "Deleted 42 audit rule records older than 90 days"
    )


@pytest.mark.django_db
def test_retrieve_execution_detail_not_found(
    management_job: models.ManagementJob,
    admin_client: APIClient,
):
    fake_uuid = "00000000-0000-0000-0000-000000000000"
    response = admin_client.get(
        f"{MANAGEMENT_JOBS_URL}/{management_job.id}"
        f"/executions/{fake_uuid}/"
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
