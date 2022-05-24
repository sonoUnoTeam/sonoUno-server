import logging
from http.client import HTTPException

from ..models import (
    Input,
    Job,
    JobIn,
    Output,
    OutputIn,
    OutputWithValue,
    Transform,
    User,
)
from ..schemas import JSONSchema

logger = logging.getLogger(__name__)


class JobBuilder:
    def __init__(self, job_in: JobIn, user: User, transform: Transform):
        self.job_in = job_in
        self.user = user
        self.transform = transform

    def create(self) -> Job:
        """Returns the Job from the input JobIn."""
        transform_inputs: dict[str, Input] = {}
        transform_outputs: dict[str, Output] = {}
        for callee in self.transform.walk_callees():
            transform_inputs |= {i.id: i for i in callee.inputs}
            transform_outputs |= {o.id: o for o in callee.outputs}

        assert self.transform.id is not None
        assert self.user.id is not None
        job = Job(
            transform_id=self.transform.id,
            user_id=self.user.id,
            inputs=self.extract_inputs(transform_inputs),
            outputs=self.extract_outputs(transform_outputs),
        )
        return job

    def extract_inputs(self, transform_inputs: dict[str, Input]) -> list[Input]:
        """Merges transform and job inputs."""
        job_inputs = {i.id: i for i in self.job_in.inputs}
        missing_ids = job_inputs.keys() - transform_inputs.keys()
        if missing_ids:
            raise HTTPException(
                400,
                f"The job input(s) {', '.join(repr(i) for i in sorted(missing_ids))} "
                f'are not specified in the transform.',
            )

        out: list[Input] = []
        for transform_input in transform_inputs.values():
            if not transform_input.modifiable:
                continue
            job_input = job_inputs.get(transform_input.id)
            if job_input:
                transform_input = transform_input.copy()
                transform_input.value = job_input.value
            out.append(transform_input)
        return out

    def extract_outputs(
        self, transform_outputs: dict[str, Output]
    ) -> list[OutputWithValue]:
        """Merges transform and job outputs."""
        job_outputs = {o.id: o for o in self.job_in.outputs}
        missing_ids = job_outputs.keys() - transform_outputs.keys()
        if missing_ids:
            raise HTTPException(
                400,
                f"The job output(s) {', '.join(repr(i) for i in sorted(missing_ids))} "
                f'are not specified in the transform.',
            )

        outputs: list[OutputWithValue] = []
        for transform_output in transform_outputs.values():
            if transform_output.transfer == 'ignore':
                continue
            output = self.extract_output(transform_output, job_outputs)
            outputs.append(output)

        return outputs

    def extract_output(
        self, transform_output: Output, job_outputs: dict[str, OutputIn]
    ) -> OutputWithValue:
        output = transform_output.dict(by_alias=True)

        job_output = job_outputs.get(transform_output.id)
        if job_output:
            for field in job_output.__fields_set__ - {'id', 'json_schema'}:
                output[field] = getattr(job_output, field)

            output['schema'] = JSONSchema(output['json']) | job_output.json_schema

        return OutputWithValue(**output)
