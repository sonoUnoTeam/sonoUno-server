import inspect
import json
import logging
from http.client import HTTPException
from types import FunctionType
from typing import Annotated, Any, Mapping, cast, get_args, get_origin

from apischema.json_schema import serialization_schema

from ..models import ExposedFunction, Input, Output, Transform, TransformIn, User
from ..types import AnyType, JSONSchema
from ..util.call_dependencies import CallDependencyResolver
from ..util.schemas import is_known_schema

logger = logging.getLogger(__name__)


def exposed(f: FunctionType) -> FunctionType:
    f.__exposed__ = True  # type: ignore[attr-defined]
    return f


def is_exposed(func: Any) -> bool:
    if not isinstance(func, FunctionType):
        return False
    return getattr(func, '__exposed__', False)


class TransformBuilder:
    def __init__(self, transform_in: TransformIn, user: User):
        self.transform_in = transform_in
        self.user = user

    def create(self) -> Transform:
        all_funcs = self.extract_all_functions()
        exposed_funcs = {f.__name__: f for f in all_funcs if is_exposed(f)}

        resolver = CallDependencyResolver(self.transform_in.source)
        function_defs = resolver.get_function_defs()
        graph = resolver.get_graph(function_defs)
        non_exposed_nodes = graph.nodes() - exposed_funcs.keys()
        resolver.remove_nodes(graph, non_exposed_nodes)
        dependencies = resolver.get_dependencies_from_graph(graph)

        if len(function_defs) == 1:
            entry_point_name = function_defs[0].name
        else:
            entry_point_name = self.transform_in.entry_point.name
            if not entry_point_name:
                raise HTTPException(
                    400, 'The name of the entry point of the pipeline is not specified.'
                )

        entry_point_func = exposed_funcs[entry_point_name]
        transform = Transform(
            name=self.transform_in.name,
            description=self.transform_in.description or entry_point_func.__doc__ or '',
            public=self.transform_in.public,
            language=self.transform_in.language,
            source=self.transform_in.source,
            entry_point=self.extract_exposed_function(
                entry_point_func,
                '',
                True,
                exposed_funcs,
                dependencies,
            ),
            user_id=self.user.id,
        )
        return transform

    def extract_all_functions(self) -> list[FunctionType]:
        locals_: dict[str, Any] = {}
        # XXX it should be executed in a container
        try:
            exec(self.transform_in.source, locals_, locals_)
        except SyntaxError:
            import sys

            print(repr(self.transform_in.source), file=sys.stderr)
            raise
        output = [
            v
            for v in locals_.values()
            if isinstance(v, FunctionType) and v.__name__ != 'exposed'
        ]
        return output

    def extract_exposed_function(
        self,
        func: FunctionType,
        caller_id: str,
        is_entry_point: bool,
        exposed_funcs: dict[str, FunctionType],
        dependencies: dict[str, list[str]],
    ) -> ExposedFunction:
        func_id = self.extract_id_from_func(func, caller_id)
        return ExposedFunction(
            id=func_id,
            name=func.__name__,
            description=self.extract_doctring_from_func(func),
            inputs=self.extract_inputs_from_func(func, func_id, is_entry_point),
            outputs=self.extract_outputs_from_func(func, func_id, is_entry_point),
            callees=self.extract_callees(func, func_id, exposed_funcs, dependencies),
        )

    def extract_id_from_func(self, func: FunctionType, caller_id: str) -> str:
        # return f'.{node.name}'
        if not caller_id:
            return func.__name__
        return f'{caller_id}.{func.__name__}'

    def extract_doctring_from_func(self, func: FunctionType) -> str:
        return func.__doc__ or ''

    def extract_inputs_from_func(
        self, func: FunctionType, callee_id: str, is_entry_point: bool
    ) -> list[Input]:
        sig = inspect.signature(func)
        return [
            self.extract_input_from_func(n, p, callee_id, is_entry_point)
            for n, p in sig.parameters.items()
        ]

    @staticmethod
    def extract_input_from_func(
        name: str, param: inspect.Parameter, callee_id: str, is_entry_point: bool
    ) -> Input:
        if param.annotation is inspect._empty:
            tp = Any
        else:
            tp = param.annotation

        try:
            json_schema = serialization_schema(tp)
        except Exception as exc:
            logger.error(
                f'Could not get serialization schema for input {name} ({tp}): '
                f'{type(exc).__name__}: {exc}'
            )
            json_schema = serialization_schema(Any)
        json_schema = cast(JSONSchema, json_schema)

        # Currently, only the inputs of the entry point can be modified
        modifiable = is_entry_point
        required = is_entry_point and param.default is param.empty
        value = None
        if param.default is not param.empty:
            try:
                json.dumps(param.default)
            except TypeError:
                # XXX default value cannot serialized and cannot be used by the client
                modifiable = False
            else:
                # XXX The default value could be different from the value actually set
                # by the caller. But we don't handle yet this case
                json_schema |= {'default': param.default}
                value = param.default

        input_ = Input(
            id=f'{callee_id}.{name}',
            name=name,
            schema=json_schema,
            modifiable=modifiable,
            required=required,
            value=value,
        )
        return input_

    def extract_outputs_from_func(
        self, func: FunctionType, callee_id: str, is_entry_point: bool
    ) -> list[Output]:
        tp_return = func.__annotations__.get('return')
        tp_outputs = self.extract_output_types(tp_return)
        return [
            self.extract_output(n, tp, callee_id, is_entry_point)
            for n, tp in tp_outputs.items()
        ]

    @staticmethod
    def extract_output_types(tp: AnyType) -> dict:
        if not tp:
            return {0: Any}

        # named tuple case
        if isinstance(tp, type) and issubclass(tp, tuple):
            fields = getattr(tp, '_fields', None)
            if fields:
                annotations = getattr(tp, '__annotations__', {})
                return {_: annotations.get(_, Any) for _ in fields}

        origin = get_origin(tp)
        if origin is None:
            return {0: tp}

        args = get_args(tp)
        if issubclass(origin, tuple):
            return {i: tp for i, tp in enumerate(args)}

        return {0: tp}

    def extract_output(
        self, name: str, tp: AnyType, callee_id: str, is_entry_point: bool
    ) -> Output:
        tp, annotations = self.extract_output_annotations(tp)

        try:
            json_schema = serialization_schema(tp)
        except Exception as exc:
            logger.exception(
                f'Could not get serialization schema for output {name} ({tp}): '
                f'{type(exc).__name__}: {exc}'
            )
            json_schema = serialization_schema(Any)
        json_schema = cast(JSONSchema, json_schema)
        json_schema.update(annotations)

        transfer = self.extract_output_transfer(json_schema, is_entry_point)

        output = Output(
            id=f'{callee_id}.{name}',
            name=name,
            schema=json_schema,
            transfer=transfer,
        )
        return output

    @staticmethod
    def extract_output_annotations(tp: AnyType) -> tuple[AnyType, JSONSchema]:
        origin = get_origin(tp)
        if origin is not Annotated:
            return tp, {}
        args = get_args(tp)
        new_origin = args[0]
        new_args = [new_origin]
        annotations: JSONSchema = {}
        for arg in args[1:]:
            if isinstance(arg, Mapping):
                annotations |= cast(JSONSchema, arg)
            else:
                new_args.append(arg)
        if len(new_args) > 1:
            tp = Annotated[tuple(new_args)]
        else:
            tp = new_origin
        return tp, annotations

    @staticmethod
    def extract_output_transfer(schema: JSONSchema, is_entry_point: bool):
        if not is_entry_point:
            # currently, we only capture the entry point outputs
            return 'ignore'

        if 'contentMediaType' not in schema:
            # we don't know what it is but we will attempt to send it as JSON
            return 'json'

        if is_known_schema(schema):
            # it means that the JSON schema is defined and valid
            return 'json'

        return 'uri'

    def extract_callees(
        self,
        func: FunctionType,
        caller_id: str,
        exposed_funcs: dict[str, FunctionType],
        dependencies: dict[str, list[str]],
    ) -> list[ExposedFunction]:
        return [
            self.extract_exposed_function(
                exposed_funcs[f],
                caller_id,
                False,
                exposed_funcs,
                dependencies,
            )
            for f in dependencies[func.__name__]
        ]
