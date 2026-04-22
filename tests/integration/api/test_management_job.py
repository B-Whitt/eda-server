#  Copyright 2026 Red Hat, Inc.
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


@pytest.fixture()
def management_job(default_organization):
    return models.ManagementJob.objects.create(
        name="Cleanup Audit Logs",
        description="Remove old audit rule logs",
        job_type=ManagementJobType.CLEANUP_AUDIT_LOGS,
        is_enabled=True,
        parameters={"retention_days": 90},
        organization=default_organization,
    )


@pytest.fixture()
def second_management_job(default_organization):
    return models.ManagementJob.objects.create(
        name="Cleanup Stale Activations",
        description="Remove stale activations",
        job_type=ManagementJobType.CLEANUP_STALE_ACTIVATIONS,
        is_enabled=False,
        organization=default_organization,
    )


@pytest.fixture()
def management_job_execution(management_job, default_organization):
    return models.ManagementJobExecution.objects.create(
        management_job=management_job,
        status=ExecutionStatus.COMPLETED,
        output="Deleted 42 records",
        organization=default_organization,
    )


# -- List --


@pytest.mark.django_db
def test_list_management_jobs(
    admin_client: APIClient,
    management_job: models.ManagementJob,
    second_management_job: models.ManagementJob,
):
    response = admin_client.get(f"{MANAGEMENT_JOBS_URL}/")
    assert response.status_code == status.HTTP_200_OK
    results = response.json()["results"]
    assert len(results) == 2


@pytest.mark.django_db
def test_list_management_jobs_filter_by_name(
    admin_client: APIClient,
    management_job: models.ManagementJob,
    second_management_job: models.ManagementJob,
):
    response = admin_client.get(f"{MANAGEMENT_JOBS_URL}/?name=Audit")
    assert response.status_code == status.HTTP_200_OK
    results = response.json()["results"]
    assert len(results) == 1
    assert results[0]["name"] == "Cleanup Audit Logs"


@pytest.mark.django_db
def test_list_management_jobs_filter_by_job_type(
    admin_client: APIClient,
    management_job: models.ManagementJob,
    second_management_job: models.ManagementJob,
):
    response = admin_client.get(
        f"{MANAGEMENT_JOBS_URL}/?job_type=cleanup_audit_logs"
    )
    assert response.status_code == status.HTTP_200_OK
    results = response.json()["results"]
    assert len(results) == 1


@pytest.mark.django_db
def test_list_management_jobs_filter_by_enabled(
    admin_client: APIClient,
    management_job: models.ManagementJob,
    second_management_job: models.ManagementJob,
):
    response = admin_client.get(f"{MANAGEMENT_JOBS_URL}/?is_enabled=false")
    assert response.status_code == status.HTTP_200_OK
    results = response.json()["results"]
    assert len(results) == 1
    assert results[0]["is_enabled"] is False


# -- Retrieve --


@pytest.mark.django_db
def test_retrieve_management_job(
    admin_client: APIClient,
    management_job: models.ManagementJob,
):
    response = admin_client.get(f"{MANAGEMENT_JOBS_URL}/{management_job.id}/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == "Cleanup Audit Logs"
    assert data["description"] == "Remove old audit rule logs"
    assert data["job_type"] == "cleanup_audit_logs"
    assert data["is_enabled"] is True
    assert data["parameters"] == {"retention_days": 90}
    assert "created_at" in data
    assert "modified_at" in data


@pytest.mark.django_db
def test_retrieve_management_job_not_found(
    admin_client: APIClient,
):
    response = admin_client.get(f"{MANAGEMENT_JOBS_URL}/99999/")
    assert response.status_code == status.HTTP_404_NOT_FOUND


# -- Partial Update --


@pytest.mark.django_db
def test_patch_management_job_is_enabled(
    admin_client: APIClient,
    management_job: models.ManagementJob,
):
    response = admin_client.patch(
        f"{MANAGEMENT_JOBS_URL}/{management_job.id}/",
        data={"is_enabled": False},
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["is_enabled"] is False
    management_job.refresh_from_db()
    assert management_job.is_enabled is False


@pytest.mark.django_db
def test_patch_management_job_parameters(
    admin_client: APIClient,
    management_job: models.ManagementJob,
):
    response = admin_client.patch(
        f"{MANAGEMENT_JOBS_URL}/{management_job.id}/",
        data={"parameters": {"retention_days": 30}},
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["parameters"] == {"retention_days": 30}
    management_job.refresh_from_db()
    assert management_job.parameters == {"retention_days": 30}


@pytest.mark.django_db
def test_patch_management_job_read_only_fields_ignored(
    admin_client: APIClient,
    management_job: models.ManagementJob,
):
    response = admin_client.patch(
        f"{MANAGEMENT_JOBS_URL}/{management_job.id}/",
        data={"name": "Hacked Name", "is_enabled": False},
    )
    assert response.status_code == status.HTTP_200_OK
    management_job.refresh_from_db()
    assert management_job.name == "Cleanup Audit Logs"
    assert management_job.is_enabled is False


# -- Launch --


@pytest.mark.django_db
def test_launch_management_job(
    admin_client: APIClient,
    management_job: models.ManagementJob,
):
    response = admin_client.post(
        f"{MANAGEMENT_JOBS_URL}/{management_job.id}/launch/"
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["status"] == "pending"
    assert data["output"] == ""
    assert data["errors"] == ""
    assert (
        models.ManagementJobExecution.objects.filter(
            management_job=management_job,
        ).count()
        == 1
    )


@pytest.mark.django_db
def test_launch_management_job_creates_multiple_executions(
    admin_client: APIClient,
    management_job: models.ManagementJob,
):
    admin_client.post(f"{MANAGEMENT_JOBS_URL}/{management_job.id}/launch/")
    admin_client.post(f"{MANAGEMENT_JOBS_URL}/{management_job.id}/launch/")
    assert (
        models.ManagementJobExecution.objects.filter(
            management_job=management_job,
        ).count()
        == 2
    )


# -- Executions List --


@pytest.mark.django_db
def test_list_executions(
    admin_client: APIClient,
    management_job: models.ManagementJob,
    management_job_execution: models.ManagementJobExecution,
):
    response = admin_client.get(
        f"{MANAGEMENT_JOBS_URL}/{management_job.id}/executions/"
    )
    assert response.status_code == status.HTTP_200_OK
    results = response.json()["results"]
    assert len(results) == 1
    assert results[0]["status"] == "completed"
    assert "output" not in results[0]


@pytest.mark.django_db
def test_list_executions_empty(
    admin_client: APIClient,
    management_job: models.ManagementJob,
):
    response = admin_client.get(
        f"{MANAGEMENT_JOBS_URL}/{management_job.id}/executions/"
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["results"] == []


# -- Execution Detail --


@pytest.mark.django_db
def test_retrieve_execution_detail(
    admin_client: APIClient,
    management_job: models.ManagementJob,
    management_job_execution: models.ManagementJobExecution,
):
    response = admin_client.get(
        f"{MANAGEMENT_JOBS_URL}/{management_job.id}/"
        f"executions/{management_job_execution.id}/"
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "completed"
    assert data["output"] == "Deleted 42 records"
    assert data["errors"] == ""


@pytest.mark.django_db
def test_retrieve_execution_detail_not_found(
    admin_client: APIClient,
    management_job: models.ManagementJob,
):
    response = admin_client.get(
        f"{MANAGEMENT_JOBS_URL}/{management_job.id}/executions/99999/"
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_retrieve_execution_wrong_job(
    admin_client: APIClient,
    management_job: models.ManagementJob,
    second_management_job: models.ManagementJob,
    management_job_execution: models.ManagementJobExecution,
):
    response = admin_client.get(
        f"{MANAGEMENT_JOBS_URL}/{second_management_job.id}/"
        f"executions/{management_job_execution.id}/"
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


# -- No Create / No Delete --


@pytest.mark.django_db
def test_create_management_job_not_allowed(
    admin_client: APIClient,
):
    response = admin_client.post(
        f"{MANAGEMENT_JOBS_URL}/",
        data={"name": "New Job"},
    )
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.django_db
def test_delete_management_job_not_allowed(
    admin_client: APIClient,
    management_job: models.ManagementJob,
):
    response = admin_client.delete(
        f"{MANAGEMENT_JOBS_URL}/{management_job.id}/"
    )
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
