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

from abc import ABC, abstractmethod


class BaseManagementJob(ABC):
    """Abstract base class for management job implementations.

    Each management job type must subclass this and implement
    ``execute()`` and ``default_parameters()``.
    """

    @abstractmethod
    def execute(self, parameters: dict) -> str:
        """Run the job.

        Args:
            parameters: Job-specific configuration dict.

        Returns:
            A human-readable output summary string.

        Raises:
            Exception: On failure — the caller records the error.
        """
        ...

    @classmethod
    @abstractmethod
    def default_parameters(cls) -> dict:
        """Return the default parameters for this job type."""
        ...
