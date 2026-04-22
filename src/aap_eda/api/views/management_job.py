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

from django_filters import rest_framework as defaultfilters
from drf_spectacular.utils import extend_schema
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from aap_eda.api import filters, serializers
from aap_eda.api.views.mixins import PartialUpdateOnlyModelMixin
from aap_eda.core import models
from aap_eda.core.enums import ExecutionStatus


class ManagementJobViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    PartialUpdateOnlyModelMixin,
    viewsets.GenericViewSet,
):
    queryset = models.ManagementJob.objects.order_by("-created_at")
    filter_backends = (defaultfilters.DjangoFilterBackend,)
    filterset_class = filters.ManagementJobFilter

    def get_serializer_class(self):
        if self.action in ("list", "retrieve"):
            return serializers.ManagementJobReadSerializer
        if self.action == "partial_update":
            return serializers.ManagementJobUpdateSerializer
        return serializers.ManagementJobReadSerializer

    def get_response_serializer_class(self):
        return serializers.ManagementJobReadSerializer

    @extend_schema(
        description="Launch an on-demand execution of a management job.",
        request=None,
        responses={
            status.HTTP_201_CREATED: serializers.ManagementJobExecutionDetailSerializer,  # noqa: E501
        },
    )
    @action(methods=["post"], detail=True)
    def launch(self, request, pk=None):
        management_job = self.get_object()
        execution = models.ManagementJobExecution.objects.create(
            management_job=management_job,
            status=ExecutionStatus.PENDING,
            organization=management_job.organization,
        )
        serializer = serializers.ManagementJobExecutionDetailSerializer(
            execution
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @extend_schema(
        description="List execution history for a management job.",
        responses={
            status.HTTP_200_OK: serializers.ManagementJobExecutionSerializer(
                many=True
            ),
        },
    )
    @action(methods=["get"], detail=True)
    def executions(self, request, pk=None):
        management_job = self.get_object()
        queryset = models.ManagementJobExecution.objects.filter(
            management_job=management_job,
        ).order_by("-created_at")
        result = self.paginate_queryset(queryset)
        serializer = serializers.ManagementJobExecutionSerializer(
            result, many=True
        )
        return self.get_paginated_response(serializer.data)

    @extend_schema(
        description="Get execution details for a management job.",
        responses={
            status.HTTP_200_OK: serializers.ManagementJobExecutionDetailSerializer,  # noqa: E501
        },
    )
    @action(
        methods=["get"],
        detail=True,
        url_path="executions/(?P<exec_id>[^/.]+)",
        url_name="execution-detail",
    )
    def execution_detail(self, request, pk=None, exec_id=None):
        management_job = self.get_object()
        try:
            execution = models.ManagementJobExecution.objects.get(
                pk=exec_id,
                management_job=management_job,
            )
        except models.ManagementJobExecution.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = serializers.ManagementJobExecutionDetailSerializer(
            execution
        )
        return Response(serializer.data)
