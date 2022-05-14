import ast
from itertools import product
from operator import itemgetter
from typing import Any, Iterable

import networkx as nx
from fastapi import HTTPException


class FunctionDefVisitor(ast.NodeVisitor):
    """Returns all the FunctionDef nodes in an AST tree.

    Functions defined inside another function are returned, but the namespace
    information is lost.
    """

    __visited_nodes: set[ast.FunctionDef]

    def visit_Module(self, node: ast.Module):
        self.__visited_nodes = set()
        self.generic_visit(node)
        return self.__visited_nodes

    def visit_FunctionDef(self, node: ast.FunctionDef) -> Any:
        self.__visited_nodes.add(node)
        super().generic_visit(node)


class FunctionDefDependencyVisitor(ast.NodeVisitor):
    """Returns all the FunctionDef nodes in an AST tree.

    Functions defined inside another function are returned, but the namespace
    information is lost.
    """

    __dependencies: list[str]

    def visit_FunctionDef(self, node: ast.FunctionDef):
        try:
            self.__dependencies
            return
        except AttributeError:
            pass

        self.__dependencies = []
        self.generic_visit(node)
        return self.__dependencies

    def visit_Call(self, node: ast.FunctionDef) -> Any:
        ast.dump(node, indent=4)
        if not isinstance(node.func, ast.Name):
            return
        self.__dependencies.append(node.func.id)
        self.generic_visit(node)


class CallDependencyResolver:
    def __init__(self, source: str):
        self.source = source

    def get_graph(self) -> nx.DiGraph:
        graph = nx.MultiDiGraph()
        tree = ast.parse(self.source)
        functions = FunctionDefVisitor().visit(tree)
        for function in functions:
            dependencies = FunctionDefDependencyVisitor().visit(function)
            graph.add_edges_from(
                (function.name, _, {'ordering': (i,)})
                for i, _ in enumerate(dependencies)
            )

        try:
            next(nx.simple_cycles(graph))
            raise HTTPException(400, 'The source has cyclic dependencies.')
        except StopIteration:
            pass
        return graph

    @staticmethod
    def remove_nodes(graph: nx.MultiDiGraph, nodes: Iterable[str]) -> None:
        for node in nodes:
            new_edges = product(
                graph.in_edges(node, data=True),
                graph.out_edges(node, data=True),
            )
            graph.add_edges_from(_contract_edges(e, f) for e, f in new_edges)
            graph.remove_node(node)

    @staticmethod
    def get_dependencies_from_graph(graph: nx.MultiDiGraph) -> dict[str, list[str]]:
        dependencies = {}
        for node in graph.nodes():
            edges = sorted(
                graph.out_edges(node, data=True), key=lambda _: _[2]['ordering']
            )
            out_nodes = [edge[1] for edge in edges]
            dependencies[node] = out_nodes
        return dependencies


DependencyEdge = tuple[str, str, dict[str, tuple[int, ...]]]


def _contract_edges(e: DependencyEdge, f: DependencyEdge):
    return e[0], f[1], {'ordering': e[2]['ordering'] + f[2]['ordering']}
