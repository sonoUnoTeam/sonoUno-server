import inspect
from typing import Any
from types import FunctionType

from apischema import schema
from apischema.json_schema import deserialization_schema
from sonouno_server.models import User
from sonouno_server.util.call_dependencies import CallDependencyResolver

from ..models import ExposedFunction, Input, Transform, TransformIn


def exposed(f: FunctionType) -> FunctionType:
    f.__exposed__ = True
    return f


def is_exposed(func: Any) -> bool:
    return isinstance(func, FunctionType) and hasattr(func, '__exposed__') and func.__exposed__


class TransformBuilder:
    def __init__(self, transform_in: TransformIn, user: User):
        self.transform_in = transform_in
        self.user = user

    def create(self) -> Transform:
        all_funcs = self.extract_all_functions()
        exposed_funcs = {f.__name__: f for f in all_funcs if is_exposed(f)}
        non_exposed_funcs = [f.__name__ for f in all_funcs if not is_exposed(f)]

        resolver = CallDependencyResolver(self.transform_in.source)
        graph = resolver.get_graph()
        resolver.remove_nodes(graph, non_exposed_funcs)
        dependencies = resolver.get_dependencies_from_graph(graph)

        def_in_source_funcs = list(graph.nodes())
        if len(def_in_source_funcs) == 1:
            entry_point_name = def_in_source_funcs[0]
        else:
            entry_point_name = self.transform_in.entry_point.name
        entry_point_func = exposed_funcs[entry_point_name]
        transform = Transform(
            name=self.transform_in.name,
            description=self.transform_in.description or entry_point_func.__doc__ or '',
            public=self.transform_in.public,
            language=self.transform_in.language,
            source = self.transform_in.source,
            entry_point=self.extract_exposed_function_model(
                entry_point_func,
                exposed_funcs,
                dependencies,
            ),
            user_id=self.user.id,
        )
        return transform

    def extract_all_functions(self) -> list[FunctionType]:
        locals_ = {}
        # XXX it should be executed in a container
        try:
            exec(self.transform_in.source, {}, locals_)
        except SyntaxError:
            import sys
            print(repr(self.transform_in.source), file=sys.stderr)
            raise
        output = [
            v for v in locals_.values()
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
            exposed_functions=self.extract_exposed_function_dependencies(
                func, exposed_funcs, dependencies),
        )

    def extract_fq_name(self, func: FunctionType) -> str:
        #return f'.{node.name}'
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
            annotation = Any
        else:
            annotation = param.annotation

        input_ = Input(
            name=name,
            fq_name=name,
            json_schema=deserialization_schema(annotation, schema=schema_for_default),
        )
        return input_

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
