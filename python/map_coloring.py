# /// script
# dependencies = [
#     "random_graph",
# ]
# requires-python = ">=3.13"
# ///

# TODO: This is a bunch of bad code, fix it, and make it better

import itertools
from collections import defaultdict
from collections.abc import Callable
import random_graph

type Node = str
type Graph = dict[Node, tuple[Node, ...]] | defaultdict[Node, list[Node]]
type Colors = dict[Node, int]
misses: int = 0


def available_colors(
    for_: tuple[Node, ...] | list[Node], n_colors: int, colors: dict[Node, int | None]
) -> set[int]:
    used_colors: set[int | None] = {colors[n] for n in for_}
    all_colors: set[int | None] = set(range(n_colors))

    # available_colors = all_colors - used_colors - None
    return all_colors.difference(used_colors, {None})  # type: ignore


def get_node_most(graph: Graph, colors: dict[Node, int | None]) -> Node:
    "get next Node with most neighbors"
    return max(colors, key=lambda k: len(graph[k]) if colors[k] is None else -1)


def get_node_least(graph: Graph, colors: dict[Node, int | None]) -> Node:
    "get next node with least colored neighbored"

    def key(k) -> int:
        if colors[k] is None:
            return len(list(filter(lambda c: colors[c] is not None, graph[k])))
        else:
            return -1

    return max(colors, key=key)


def color_graph(
    graph: Graph, n_colors: int, colors: dict[Node, int | None]
) -> Colors | None:
    global misses  # for debugging purposes

    node: Node = get_node(graph, colors)
    if colors[node] is not None:
        return colors  # type: ignore

    for color in available_colors(graph[node], n_colors, colors):
        colors[node] = color  # assign this color to node
        misses += 1

        map_colors = color_graph(graph, n_colors, colors)
        if map_colors is not None:  # if possible configuration
            return map_colors

        colors[node] = None  # remove color before backtracking

    return None  # can't assign colors, backtrack


def get_color_name(color_names: list, idx: int):
    return color_names[idx] if idx < len(color_names) else idx


# 3 sample graphs
graph1: Graph = dict(  # An exemplary Graph
    Arad=("Zerind", "Sibiu", "Timisoara"),
    Bucharest=("Urziceni", "Pitesti", "Giurgiu", "Fagaras"),
    Craiova=("Drobeta", "Rimnicu", "Pitesti"),
    Drobeta=("Craiova", "Mehadia"),
    Eforie=("Hirsova",),
    Fagaras=("Bucharest", "Sibiu"),
    Hirsova=("Eforie", "Urziceni"),
    Iasi=("Vaslui", "Neamt"),
    Lugoj=("Timisoara", "Mehadia"),
    Oradea=("Zerind", "Sibiu"),
    Pitesti=("Bucharest", "Craiova", "Rimnicu"),
    Rimnicu=("Craiova", "Pitesti", "Sibiu"),
    Urziceni=("Bucharest", "Hirsova", "Vaslui"),
    Zerind=("Arad", "Oradea"),
    Sibiu=("Arad", "Fagaras", "Oradea", "Rimnicu"),
    Timisoara=("Arad", "Lugoj"),
    Giurgiu=("Bucharest",),
    Mehadia=("Drobeta", "Lugoj"),
    Vaslui=("Iasi", "Urziceni"),
    Neamt=("Iasi",),
)

graph2: Graph = dict(  # A fully connected graph
    Arad=("Bucharest", "Craiova", "Drobeta", "Rimnicu", "Timisoara", "Neamt"),
    Bucharest=("Arad", "Craiova", "Drobeta", "Rimnicu", "Timisoara", "Neamt"),
    Craiova=("Arad", "Bucharest", "Drobeta", "Rimnicu", "Timisoara", "Neamt"),
    Drobeta=("Arad", "Bucharest", "Craiova", "Rimnicu", "Timisoara", "Neamt"),
    Rimnicu=("Arad", "Bucharest", "Craiova", "Drobeta", "Timisoara", "Neamt"),
    Timisoara=("Arad", "Bucharest", "Craiova", "Drobeta", "Rimnicu", "Neamt"),
    Neamt=("Arad", "Bucharest", "Craiova", "Drobeta", "Rimnicu", "Timisoara"),
)

graph3: Graph = dict(  # A test graph
    A=("B", "C"),
    B=("D", "E"),
    C=("A", "D", "F", "G"),
    D=("B", "C", "H"),
    E=("B", "H"),
    F=("C", "G", "I"),
    G=("C", "F", "I"),
    H=("D", "E"),
    I=("F", "G"),
)

# which get_node to use
get_node: Callable[..., str] = get_node_least


def color(graph: Graph, color_names: list = []) -> Colors:
    global misses
    misses = 0

    colors: dict = dict.fromkeys(graph.keys(), None)
    colors[get_node(graph, colors)] = 0  # set default color to first item

    for n_colors in itertools.count(1):  # try n_colors from 1 to +inf
        map_colors = color_graph(graph, n_colors=n_colors, colors=colors)

        print(f"{misses = }")
        if map_colors is not None:  # until map can be colored
            return {k: get_color_name(color_names, v) for k, v in map_colors.items()}

    assert False  # for loop must return


def benchmark() -> None:
    global get_node
    graph: defaultdict[Node, list[Node]] = defaultdict(list)

    degrees: tuple = (4,) * 12 + (10,) * 6 + (5,) * 14
    edges = random_graph.sample_simple_graph(degrees)

    for from_, to_ in edges:
        graph[str(from_)].append(str(to_))
        graph[str(to_)].append(str(from_))

    print("get_node_least")
    get_node = get_node_least
    color(graph)

    print("get_node_most")
    get_node = get_node_most
    color(graph)


def main() -> None:
    # print(color(graph1))
    # print(color(graph2))
    # print(color(graph3))
    benchmark()


if __name__ == "__main__":
    main()
