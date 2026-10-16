"""BFS, DFS and UCS search algorithms for the N-puzzle.

Each search returns a rich result: the reconstructed solution path, the
order in which states were expanded/generated (search exploration), the
frontier size over time (frontier history) and real statistics. Nothing
here is simulated — every number comes from the actual search run.
"""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field
from heapq import heappop, heappush
from typing import Dict, List, Optional, Sequence, Tuple

from .puzzle import State, is_solvable, moves_between, neighbors

ALGORITHMS = ("bfs", "dfs", "ucs")

# Defaults chosen so a full 8-puzzle search never exhausts memory or
# floods the JSON payload, while still covering worst-case boards.
DEFAULT_LIMITS = {
    "max_expanded": 200_000,
    "max_depth": 200,
    "max_trace": 1200,
}


@dataclass
class SearchLimits:
    max_expanded: int = DEFAULT_LIMITS["max_expanded"]
    max_depth: int = DEFAULT_LIMITS["max_depth"]
    max_trace: int = DEFAULT_LIMITS["max_trace"]

    @classmethod
    def from_dict(cls, raw: Optional[dict]) -> "SearchLimits":
        raw = raw or {}
        def _int(key: str) -> int:
            val = raw.get(key, DEFAULT_LIMITS[key])
            if not isinstance(val, int) or isinstance(val, bool) or val <= 0:
                raise ValueError(f"limits.{key} must be a positive integer")
            return val
        return cls(max_expanded=_int("max_expanded"),
                   max_depth=_int("max_depth"),
                   max_trace=_int("max_trace"))


@dataclass
class Node:
    state: State
    parent: Optional["Node"]
    move: Optional[str]   # move applied at parent to reach this node
    depth: int
    cost: int             # path cost from the root (UCS)


@dataclass
class SearchResult:
    algorithm: str
    start: State
    goal: State
    solvable: bool
    solved: bool = False
    reason: Optional[str] = None          # 'unsolvable' | 'limit_exceeded'
    solution: List[State] = field(default_factory=list)
    moves: List[str] = field(default_factory=list)
    path_cost: int = 0
    stats: Dict[str, int] = field(default_factory=dict)
    # Exploration trace (capped): nodes array + ordered expand/generate events.
    nodes: List[dict] = field(default_factory=list)
    events: List[dict] = field(default_factory=list)
    trace_truncated: bool = False

    def to_dict(self) -> dict:
        return {
            "algorithm": self.algorithm,
            "start": list(self.start),
            "goal": list(self.goal),
            "solvable": self.solvable,
            "solved": self.solved,
            "reason": self.reason,
            "solution": {
                "path": [list(s) for s in self.solution],
                "moves": self.moves,
                "length": max(0, len(self.solution) - 1),
                "path_cost": self.path_cost,
            },
            "stats": self.stats,
            "nodes": self.nodes,
            "events": self.events,
            "trace_truncated": self.trace_truncated,
        }


def _reconstruct(node: Node) -> Tuple[List[State], List[str]]:
    states: List[State] = []
    moves: List[str] = []
    cur: Optional[Node] = node
    while cur is not None:
        states.append(cur.state)
        if cur.parent is not None and cur.move is not None:
            moves.append(cur.move)
        cur = cur.parent
    states.reverse()
    moves.reverse()
    return states, moves


class _Recorder:
    """Collects exploration events, capping payload size at ``max_trace``."""

    def __init__(self, max_trace: int):
        self.max_trace = max_trace
        self.nodes: List[dict] = []
        self.events: List[dict] = []
        self.truncated = False
        self._id_of: Dict[State, int] = {}

    def register(self, node: Node) -> int:
        nid = len(self.nodes)
        self._id_of[node.state] = nid
        self.nodes.append({
            "id": nid,
            "state": list(node.state),
            "parent": self._id_of.get(node.parent.state) if node.parent else None,
            "move": node.move,
            "depth": node.depth,
            "cost": node.cost,
        })
        return nid

    def id_of(self, state: State) -> Optional[int]:
        return self._id_of.get(state)

    def event(self, kind: str, node: Node, frontier_size: int) -> None:
        if len(self.events) >= self.max_trace:
            self.truncated = True
            return
        self.events.append({
            "type": kind,                     # 'expand' | 'generate'
            "id": self._id_of.get(node.state),
            "state": list(node.state),
            "depth": node.depth,
            "frontier_size": frontier_size,
        })


def _finish(result: SearchResult, expanded: int, generated: int,
            max_frontier: int, max_depth_seen: int, elapsed_ms: float,
            recorder: _Recorder) -> SearchResult:
    result.stats = {
        "nodes_expanded": expanded,
        "nodes_generated": generated,
        "max_frontier_size": max_frontier,
        "max_depth": max_depth_seen,
        "elapsed_ms": round(elapsed_ms, 3),
    }
    result.nodes = recorder.nodes
    result.events = recorder.events
    result.trace_truncated = recorder.truncated or result.trace_truncated
    return result


def _solve_core(start: State, goal: State, algorithm: str,
                limits: SearchLimits) -> SearchResult:
    result = SearchResult(algorithm=algorithm, start=start, goal=goal,
                          solvable=True)
    if start == goal:
        result.solved = True
        result.solution = [start]
        result.moves = []
        result.path_cost = 0
        t0 = time.perf_counter()
        rec = _Recorder(limits.max_trace)
        rec.register(Node(start, None, None, 0, 0))
        return _finish(result, 0, 0, 1, 0,
                       (time.perf_counter() - t0) * 1000, rec)

    t0 = time.perf_counter()
    rec = _Recorder(limits.max_trace)
    root = Node(start, None, None, 0, 0)
    rec.register(root)

    expanded = 0
    generated = 0
    max_frontier = 0
    max_depth_seen = 0
    visited: Dict[State, Node] = {start: root}
    goal_node: Optional[Node] = None

    if algorithm == "bfs":
        frontier = deque([root])
        frontier_size = 1
        max_frontier = 1
        while frontier:
            max_frontier = max(max_frontier, frontier_size)
            if expanded >= limits.max_expanded:
                result.reason = "limit_exceeded"
                break
            node = frontier.popleft()
            frontier_size -= 1
            rec.event("expand", node, frontier_size)
            expanded += 1
            if node.state == goal:
                goal_node = node
                break
            for succ, mv in neighbors(node.state):
                if succ in visited:
                    continue
                generated += 1
                child = Node(succ, node, mv, node.depth + 1, node.cost + 1)
                visited[succ] = child
                rec.register(child)
                if child.depth > limits.max_depth:
                    continue
                max_depth_seen = max(max_depth_seen, child.depth)
                frontier.append(child)
                frontier_size += 1
                rec.event("generate", child, frontier_size)

    elif algorithm == "dfs":
        # Iterative-free explicit-stack DFS. A visited set guarantees
        # termination on the finite state space.
        stack = [root]
        frontier_size = 1
        max_frontier = 1
        while stack:
            max_frontier = max(max_frontier, frontier_size)
            if expanded >= limits.max_expanded:
                result.reason = "limit_exceeded"
                break
            node = stack.pop()
            frontier_size -= 1
            rec.event("expand", node, frontier_size)
            expanded += 1
            if node.state == goal:
                goal_node = node
                break
            succs = neighbors(node.state)
            # Push in reverse so the first legal move is explored first,
            # matching the documented Up/Down/Left/Right preference.
            for succ, mv in reversed(succs):
                if succ in visited:
                    continue
                generated += 1
                child = Node(succ, node, mv, node.depth + 1, node.cost + 1)
                visited[succ] = child
                rec.register(child)
                if child.depth > limits.max_depth:
                    continue
                max_depth_seen = max(max_depth_seen, child.depth)
                stack.append(child)
                frontier_size += 1
                rec.event("generate", child, frontier_size)

    elif algorithm == "ucs":
        # Uniform-cost search: every move costs 1, so the priority is the
        # path cost. Correctness holds for the classic unit-cost puzzle.
        heap: List[Tuple[int, int, Node]] = []
        counter = 0
        heappush(heap, (root.cost, counter, root))
        frontier_size = 1
        max_frontier = 1
        while heap:
            max_frontier = max(max_frontier, frontier_size)
            if expanded >= limits.max_expanded:
                result.reason = "limit_exceeded"
                break
            _, _, node = heappop(heap)
            frontier_size -= 1
            rec.event("expand", node, frontier_size)
            expanded += 1
            if node.state == goal:
                goal_node = node
                break
            for succ, mv in neighbors(node.state):
                if succ in visited:
                    continue
                generated += 1
                child = Node(succ, node, mv, node.depth + 1, node.cost + 1)
                visited[succ] = child
                rec.register(child)
                if child.depth > limits.max_depth:
                    continue
                max_depth_seen = max(max_depth_seen, child.depth)
                counter += 1
                heappush(heap, (child.cost, counter, child))
                frontier_size += 1
                rec.event("generate", child, frontier_size)
    else:
        raise ValueError(f"unknown algorithm: {algorithm}")

    elapsed = (time.perf_counter() - t0) * 1000

    if goal_node is not None:
        result.solved = True
        states, moves = _reconstruct(goal_node)
        # Cross-check the reconstruction against real adjacency; a broken
        # parent chain is a hard error, never silently shipped.
        for a, b in zip(states, states[1:]):
            moves_between(a, b)
        result.solution = states
        result.moves = moves
        result.path_cost = goal_node.cost
    elif result.reason is None:
        result.reason = "exhausted"

    return _finish(result, expanded, generated, max_frontier, max_depth_seen,
                   elapsed, rec)


def solve(start: State, goal: State, algorithm: str,
          limits: Optional[SearchLimits] = None) -> SearchResult:
    """Run a search. Unsolvable boards short-circuit without searching."""
    algorithm = (algorithm or "").lower()
    if algorithm not in ALGORITHMS:
        raise ValueError(f"algorithm must be one of {', '.join(ALGORITHMS)}")
    limits = limits or SearchLimits()
    if not is_solvable(start, goal):
        return SearchResult(algorithm=algorithm, start=start, goal=goal,
                            solvable=False, solved=False,
                            reason="unsolvable",
                            stats={"nodes_expanded": 0, "nodes_generated": 0,
                                   "max_frontier_size": 0, "max_depth": 0,
                                   "elapsed_ms": 0.0})
    return _solve_core(start, goal, algorithm, limits)


def compare(start: State, goal: State, algorithms: Sequence[str],
            limits: Optional[SearchLimits] = None) -> List[SearchResult]:
    limits = limits or SearchLimits()
    out: List[SearchResult] = []
    seen = set()
    for name in algorithms:
        name = (name or "").lower()
        if name in seen:
            continue
        seen.add(name)
        if name not in ALGORITHMS:
            raise ValueError(f"unknown algorithm in compare: {name}")
        out.append(solve(start, goal, name, limits))
    return out
