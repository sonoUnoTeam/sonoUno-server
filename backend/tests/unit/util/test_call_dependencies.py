import networkx as nx
import pytest

from sonouno_server.util.call_dependencies import (
    CallDependencyResolver,
    _contract_edges,
)


def get_graph(values):
    values = [(a, b, {'ordering': c}) for a, b, c in values]
    graph = nx.MultiDiGraph()
    graph.add_edges_from(values)
    return graph


def assert_graph_equals(graph1, graph2):
    def get_edges(graph):
        return {(a, b, c['ordering']) for a, b, c in graph.edges(data=True)}

    assert set(graph1.nodes()) == set(graph2.nodes())
    assert get_edges(graph1) == get_edges(graph2)


GRAPH = [(0, 1, (2, 3)), (1, 2, (2,)), (1, 3, (1,)), (0, 3, (1, 1)), (0, 3, (3, 1))]


@pytest.mark.parametrize(
    'node, expected',
    [
        (1, [(0, 2, (2, 3, 2)), (0, 3, (2, 3, 1)), (0, 3, (1, 1)), (0, 3, (3, 1))]),
    ],
)
def test_remove_nodes(node, expected):
    graph = get_graph(GRAPH)
    CallDependencyResolver.remove_nodes(graph, [node])
    expected_graph = get_graph(expected)
    assert_graph_equals(graph, expected_graph)


def test_dependencies():
    graph = get_graph(GRAPH)
    dependencies = CallDependencyResolver.get_dependencies_from_graph(graph)
    assert dependencies == {
        0: [3, 1, 3],
        1: [3, 2],
        2: [],
        3: [],
    }


def test_contract_edges():
    edge1 = ('a', 'b', {'ordering': (1, 2)})
    edge2 = ('b', 'c', {'ordering': (5,)})
    assert _contract_edges(edge1, edge2) == ('a', 'c', {'ordering': (1, 2, 5)})


def test_get_graph():
    source = """
def a():
    b()

def b():
    c()
    d()
    c()

def c():
    d()

def d():
    pass
    """
    expected = [
        ('a', 'b', (0,)),
        ('b', 'c', (0,)),
        ('b', 'd', (1,)),
        ('b', 'c', (2,)),
        ('c', 'd', (0,)),
    ]
    resolver = CallDependencyResolver(source)
    function_defs = resolver.get_function_defs()
    actual_graph = resolver.get_graph(function_defs)
    expected_graph = get_graph(expected)
    assert_graph_equals(actual_graph, expected_graph)
