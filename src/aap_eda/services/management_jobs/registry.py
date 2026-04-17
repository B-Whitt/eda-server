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

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .base import BaseManagementJob


class ManagementJobRegistry:
    """Registry mapping job type strings to job implementation classes."""

    def __init__(self):
        self._registry: dict[str, type[BaseManagementJob]] = {}

    def register(
        self, job_type: str, job_class: type[BaseManagementJob]
    ) -> None:
        self._registry[job_type] = job_class

    def get(self, job_type: str) -> type[BaseManagementJob]:
        try:
            return self._registry[job_type]
        except KeyError:
            raise ValueError(
                f"Unknown management job type: {job_type!r}. "
                f"Registered types: {list(self._registry)}"
            )

    def is_registered(self, job_type: str) -> bool:
        return job_type in self._registry

    @property
    def registered_types(self) -> list[str]:
        return list(self._registry)


# Module-level singleton
management_job_registry = ManagementJobRegistry()
