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

from rest_framework import serializers

from aap_eda.core import models


class ManagementJobReadSerializer(serializers.ModelSerializer):
    """Serializer for reading management job details."""

    class Meta:
        model = models.ManagementJob
        fields = [
            "id",
            "name",
            "description",
            "job_type",
            "is_enabled",
            "parameters",
            "organization_id",
            "created_at",
            "modified_at",
        ]
        read_only_fields = [
            "id",
            "name",
            "description",
            "job_type",
            "organization_id",
            "created_at",
            "modified_at",
        ]


class ManagementJobUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating management job settings."""

    class Meta:
        model = models.ManagementJob
        fields = [
            "is_enabled",
            "parameters",
        ]


class ManagementJobExecutionReadSerializer(serializers.ModelSerializer):
    """Serializer for reading management job execution details."""

    class Meta:
        model = models.ManagementJobExecution
        fields = [
            "id",
            "management_job_id",
            "status",
            "started_at",
            "finished_at",
            "output",
            "errors",
            "created_by",
            "organization_id",
        ]
        read_only_fields = fields
