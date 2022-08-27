from __future__ import annotations

import typing
from collections.abc import Mapping
from typing import Any

from fastapi import HTTPException

if typing.TYPE_CHECKING:
    from .models import Job, Transform


class LocalExecutor:
    """Runs the transform in the job creation request.

    It should only be used for testing purposes.
    """

    def __init__(self, job: Job, transform: Transform):
        self.job = job
        self.transform = transform

    def run(self) -> Mapping[str, Any]:
        """Executes the transform code."""
        # Very naively injects the inputs and extracts the outputs of the job.
        locals_ = {'zzz_inputs': self.prepare_inputs()}
        source = (
            self.transform.source
            + f'\nzzz_results = {self.transform.entry_point.name}(**zzz_inputs)\n'
        )
        exec(source, locals_, locals_)
        return self.prepare_outputs(locals_['zzz_results'])

    def prepare_inputs(self) -> Mapping[str, Any]:
        """Packs the entry point inputs."""
        # XXX only the entry point inputs can be modified
        return {i.name: i.value for i in self.job.inputs}

    def prepare_outputs(self, results: Any) -> Mapping[str, Any]:
        """Unpacks the value returned by the transform entry point.

        Arguments:
            results: The returned values of the transform entry point.

        Returns:
            A mapping output id to value.
        """
        expected_outputs = self.transform.entry_point.outputs
        if len(expected_outputs) == 0:
            return {}
        if len(expected_outputs) == 1:
            return {expected_outputs[0].id: results}
        if not isinstance(results, tuple) or len(expected_outputs) != len(results):
            raise HTTPException(
                422, 'The entry point does not return the expected number of outputs.'
            )
        return dict(zip((o.id for o in self.transform.entry_point.outputs), results))
