import inspect
import logging
from types import FunctionType
from typing import Any, get_args, get_origin

from apischema import schema
from apischema.json_schema import serialization_schema

from ..models import ExposedFunction, Input, Output, Transform, TransformIn, User
from ..types import AnyType
from ..util.call_dependencies import CallDependencyResolver

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
        entry_point_func = exposed_funcs[entry_point_name]
        transform = Transform(
            name=self.transform_in.name,
            description=self.transform_in.description or entry_point_func.__doc__ or '',
            public=self.transform_in.public,
            language=self.transform_in.language,
            source=self.transform_in.source,
            entry_point=self.extract_exposed_function_model(
                entry_point_func,
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

    def extract_exposed_function_model(
        self,
        func: FunctionType,
        exposed_funcs: dict[str, FunctionType],
        dependencies: dict[str, list[str]],
    ) -> ExposedFunction:
        return ExposedFunction(
            name=func.__name__,
            fq_name=self.extract_fq_name(func),
            description=self.extract_doctring_from_func(func),
            inputs=self.extract_inputs_from_func(func),
            outputs=self.extract_outputs_from_func(func),
            exposed_functions=self.extract_exposed_function_dependencies(
                func, exposed_funcs, dependencies
            ),
        )

    def extract_fq_name(self, func: FunctionType) -> str:
        # return f'.{node.name}'
        return func.__name__

    def extract_doctring_from_func(self, func: FunctionType) -> str:
        return func.__doc__ or ''

    def extract_inputs_from_func(self, func: FunctionType) -> list[Input]:
        sig = inspect.signature(func)
        return [self.extract_input_from_func(n, p) for n, p in sig.parameters.items()]

    @staticmethod
    def extract_input_from_func(name: str, param: inspect.Parameter) -> Input:
        if param.default is param.empty:
            schema_for_default = None
        else:
            schema_for_default = schema(default=param.default)
        if param.annotation is inspect._empty:
            tp = Any
        else:
            tp = param.annotation

        try:
            json_schema = serialization_schema(tp, schema=schema_for_default)
        except Exception as exc:
            logger.error(
                f'Could not get serialization schema for input {name} ({tp}): '
                f'{type(exc).__name__}: {exc}'
            )
            json_schema = serialization_schema(Any, schema=schema_for_default)

        input_ = Input(
            name=name,
            fq_name=name,
            json_schema=json_schema,
        )
        return input_

    def extract_outputs_from_func(self, func: FunctionType) -> list[Output]:
        tp_return = func.__annotations__.get('return')
        tp_outputs = self.extract_output_types(tp_return)
        return [self.extract_output(n, tp) for n, tp in tp_outputs.items()]

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

    @staticmethod
    def extract_output(name: str, tp: AnyType) -> Output:
        try:
            json_schema = serialization_schema(tp)
        except Exception as exc:
            logger.error(
                f'Could not get serialization schema for output {name} ({tp}): '
                f'{type(exc).__name__}: {exc}'
            )
            json_schema = serialization_schema(Any)
        output = Output(
            name=name,
            json_schema=json_schema,
        )
        return output

    def extract_exposed_function_dependencies(
        self,
        func: FunctionType,
        exposed_funcs: dict[str, FunctionType],
        dependencies: dict[str, list[str]],
    ) -> list[ExposedFunction]:
        return [
            self.extract_exposed_function_model(
                exposed_funcs[f],
                exposed_funcs,
                dependencies,
            )
            for f in dependencies[func.__name__]
        ]
