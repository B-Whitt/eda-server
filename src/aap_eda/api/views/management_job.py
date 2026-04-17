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

from django.shortcuts import get_object_or_404
from django.utils import timezone
from django_filters import rest_framework as defaultfilters
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from aap_eda.api import filters, serializers
from aap_eda.core import models
from aap_eda.core.enums import ExecutionStatus
from aap_eda.services.management_jobs import management_job_registry

logger = logging.getLogger(__name__)


@extend_schema_view(
    list=extend_schema(
        description="List all management jobs",
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                serializers.ManagementJobReadSerializer,
                description="Return a list of management jobs.",
            ),
        },
        extensions={
            "x-ai-description": (
                "List management jobs. Returns management job records "
                "with their configuration. Supports filtering by name, "
                "job_type, and is_enabled."
            )
        },
    ),
    retrieve=extend_schema(
        description="Get a management job by its id",
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                serializers.ManagementJobReadSerializer,
                description="Return the management job by its id.",
            ),
        },
    ),
    partial_update=extend_schema(
        description="Update management job settings",
        request=serializers.ManagementJobUpdateSerializer,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                serializers.ManagementJobReadSerializer,
                description="Return the updated management job.",
            ),
        },
    ),
)
class ManagementJobViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = models.ManagementJob.objects.order_by("name")
    filter_backends = (defaultfilters.DjangoFilterBackend,)
    filterset_class = filters.ManagementJobFilter
    rbac_action = None
    http_method_names = ["get", "patch", "post", "head", "options"]

    def get_serializer_class(self):
        if self.action == "partial_update":
            return serializers.ManagementJobUpdateSerializer
        if self.action in ("executions", "execution_detail"):
            return serializers.ManagementJobExecutionReadSerializer
        return serializers.ManagementJobReadSerializer

    @extend_schema(
        description="Trigger an on-demand execution of a management job",
        request=None,
        responses={
            status.HTTP_202_ACCEPTED: OpenApiResponse(
                serializers.ManagementJobExecutionReadSerializer,
                description="Management job execution started.",
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                None,
                description="Management job is disabled.",
            ),
        },
    )
    @action(detail=True, methods=["post"])
    def launch(self, request, pk=None):
        management_job = self.get_object()

        if not management_job.is_enabled:
            return Response(
                {"detail": "Management job is disabled."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        execution = models.ManagementJobExecution.objects.create(
            management_job=management_job,
            status=ExecutionStatus.RUNNING,
            started_at=timezone.now(),
            created_by=request.user,
            organization=management_job.organization,
        )

        logger.info(
            "Management job '%s' (id=%s) launched by user '%s', "
            "execution_id=%s",
            management_job.name,
            management_job.id,
            request.user.username,
            execution.id,
        )

        # Execute synchronously (phase 1).
        # Phase 2 will move this to Celery.
        try:
            job_class = management_job_registry.get(management_job.job_type)
            job = job_class()
            output = job.execute(management_job.parameters)
            execution.status = ExecutionStatus.COMPLETED
            execution.output = output
        except Exception as exc:
            execution.status = ExecutionStatus.FAILED
            execution.errors = str(exc)
            logger.exception(
                "Management job '%s' failed: %s",
                management_job.name,
                exc,
            )
        finally:
            execution.finished_at = timezone.now()
            execution.save(
                update_fields=["status", "output", "errors", "finished_at"]
            )

        serializer = serializers.ManagementJobExecutionReadSerializer(
            execution
        )
        resp_status = (
            status.HTTP_202_ACCEPTED
            if execution.status == ExecutionStatus.COMPLETED
            else status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        return Response(serializer.data, status=resp_status)

    @extend_schema(
        description="List execution history for a management job",
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                serializers.ManagementJobExecutionReadSerializer(many=True),
                description="Return execution history.",
            ),
        },
        parameters=[
            OpenApiParameter(
                name="id",
                type=int,
                location=OpenApiParameter.PATH,
                description=(
                    "A unique integer value identifying "
                    "this management job."
                ),
            ),
        ],
    )
    @action(
        detail=False,
        url_path="(?P<id>[^/.]+)/executions",
    )
    def executions(self, request, id=None):
        management_job = get_object_or_404(models.ManagementJob, pk=id)
        queryset = models.ManagementJobExecution.objects.filter(
            management_job=management_job,
        ).order_by("-started_at")

        results = self.paginate_queryset(queryset)
        serializer = serializers.ManagementJobExecutionReadSerializer(
            results, many=True
        )
        return self.get_paginated_response(serializer.data)

    @extend_schema(
        description="Get execution details for a management job",
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                serializers.ManagementJobExecutionReadSerializer,
                description="Return execution details.",
            ),
        },
        parameters=[
            OpenApiParameter(
                name="id",
                type=int,
                location=OpenApiParameter.PATH,
                description=(
                    "A unique integer value identifying "
                    "this management job."
                ),
            ),
            OpenApiParameter(
                name="exec_id",
                type=str,
                location=OpenApiParameter.PATH,
                description="UUID of the execution.",
            ),
        ],
    )
    @action(
        detail=False,
        url_path="(?P<id>[^/.]+)/executions/(?P<exec_id>[^/.]+)",
    )
    def execution_detail(self, request, id=None, exec_id=None):
        management_job = get_object_or_404(models.ManagementJob, pk=id)
        execution = get_object_or_404(
            models.ManagementJobExecution,
            pk=exec_id,
            management_job=management_job,
        )
        serializer = serializers.ManagementJobExecutionReadSerializer(
            execution
        )
        return Response(serializer.data)
