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

from rest_framework import serializers

from aap_eda.core import models

__all__ = (
    "ManagementJobReadSerializer",
    "ManagementJobUpdateSerializer",
    "ManagementJobExecutionSerializer",
    "ManagementJobExecutionDetailSerializer",
)


class ManagementJobReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ManagementJob
        read_only_fields = [
            "id",
            "name",
            "description",
            "job_type",
            "organization",
            "created_at",
            "modified_at",
        ]
        fields = [
            "is_enabled",
            "parameters",
            *read_only_fields,
        ]


class ManagementJobUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ManagementJob
        fields = ["is_enabled", "parameters"]


class ManagementJobExecutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ManagementJobExecution
        read_only_fields = [
            "id",
            "status",
            "started_at",
            "finished_at",
            "created_at",
        ]
        fields = read_only_fields


class ManagementJobExecutionDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ManagementJobExecution
        read_only_fields = [
            "id",
            "status",
            "started_at",
            "finished_at",
            "output",
            "errors",
            "created_at",
        ]
        fields = read_only_fields
