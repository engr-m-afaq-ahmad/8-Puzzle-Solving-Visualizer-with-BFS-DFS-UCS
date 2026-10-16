"""Tests for BFS / DFS / UCS correctness, metrics and limits."""

import pytest

from backend.algorithms import SearchLimits, compare, solve
from backend.puzzle import PuzzleError, neighbors, parse_board

GOAL = (1, 2, 3, 4, 5, 6, 7, 8, 0)
EASY = (1, 2, 3, 4, 0, 6, 7, 5, 8)          # optimal = 4 moves
MEDIUM = (1, 2, 3, 4, 0, 6, 7, 8, 5)        # optimal = 2 moves
UNSOLVABLE = (1, 2, 3, 4, 5, 6, 8, 7, 0)
HARD = (8, 6, 7, 2, 5, 4, 3, 0, 1)          # 31-move worst case (God's number)


def assert_valid_path(result, start, goal):
    path = result.solution
    assert path[0] == start
    assert path[-1] == goal
    for a, b in zip(path, path[1:]):
        assert b in [s for s, _ in neighbors(a)], "path step is not a legal move"
    assert len(result.moves) == len(path) - 1
    assert result.path_cost == len(result.moves)


@pytest.mark.parametrize("algo", ["bfs", "dfs", "ucs"])
def test_solves_easy(algo):
    r = solve(EASY, GOAL, algo)
    assert r.solved and r.solvable
    assert_valid_path(r, EASY, GOAL)


@pytest.mark.parametrize("algo", ["bfs", "ucs"])
def test_optimal_length(algo):
    # BFS and UCS (unit cost) must find the true optimal solution.
    r = solve(EASY, GOAL, algo)
    assert r.solution and len(r.moves) == 4
    r2 = solve(MEDIUM, GOAL, algo)
    assert len(r2.moves) == 2


def test_bfs_ucs_agree_on_hard():
    b = solve(HARD, GOAL, "bfs")
    u = solve(HARD, GOAL, "ucs")
    assert b.solved and u.solved
    assert len(b.moves) == 31
    assert len(u.moves) == len(b.moves)


def test_dfs_finds_a_valid_but_maybe_suboptimal_path():
    r = solve(EASY, GOAL, "dfs")
    assert r.solved
    assert_valid_path(r, EASY, GOAL)
    assert len(r.moves) >= 4  # DFS is not guaranteed optimal


def test_unsolvable_short_circuits():
    for algo in ("bfs", "dfs", "ucs"):
        r = solve(UNSOLVABLE, GOAL, algo)
        assert not r.solvable and not r.solved
        assert r.reason == "unsolvable"
        assert r.stats["nodes_expanded"] == 0
        assert r.solution == []


def test_already_solved():
    r = solve(GOAL, GOAL, "bfs")
    assert r.solved
    assert r.solution == [GOAL]
    assert r.moves == []
    assert r.path_cost == 0
    assert r.stats["nodes_expanded"] == 0


def test_arbitrary_goal():
    goal = (1, 2, 3, 4, 5, 6, 8, 7, 0)
    start = (1, 2, 3, 4, 5, 6, 0, 8, 7)   # blank moved: solvable vs goal2
    r = solve(start, goal, "bfs")
    assert r.solved
    assert_valid_path(r, start, goal)
    assert len(r.moves) == 1


def test_unknown_algorithm():
    with pytest.raises(ValueError):
        solve(EASY, GOAL, "astar")


def test_metrics_are_real_and_consistent():
    r = solve(EASY, GOAL, "bfs")
    s = r.stats
    assert s["nodes_expanded"] > 0
    assert s["nodes_generated"] >= s["nodes_expanded"]
    assert s["max_frontier_size"] >= 1
    assert s["elapsed_ms"] >= 0
    # Trace event counts must match the reported expansion count prefix.
    expands = [e for e in r.events if e["type"] == "expand"]
    assert len(expands) == min(s["nodes_expanded"], len(r.events))


def test_trace_is_capped():
    limits = SearchLimits(max_expanded=200_000, max_depth=200, max_trace=25)
    r = solve(HARD, GOAL, "bfs", limits)
    assert r.solved
    assert len(r.events) <= 25
    assert r.trace_truncated is True


def test_expansion_limit_aborts():
    limits = SearchLimits(max_expanded=5, max_depth=200, max_trace=100)
    r = solve(HARD, GOAL, "bfs", limits)
    assert not r.solved
    assert r.reason == "limit_exceeded"
    assert r.stats["nodes_expanded"] <= 5


def test_frontier_history_reconstructs():
    # Replaying generate/expand events must reproduce the recorded
    # frontier sizes exactly — this is the data the UI draws.
    r = solve(EASY, GOAL, "bfs")
    frontier = set()
    size = 0
    for e in r.events:
        if e["type"] == "generate":
            frontier.add(e["id"])
            size += 1
        elif e["type"] == "expand" and e["id"] in frontier:
            frontier.discard(e["id"])
            size -= 1
        assert size == e["frontier_size"]


def test_nodes_have_parent_pointers():
    r = solve(HARD, GOAL, "bfs")
    ids = {n["id"] for n in r.nodes}
    for n in r.nodes:
        assert n["id"] in ids
        if n["parent"] is not None:
            assert n["parent"] in ids
            assert n["depth"] == next(m["depth"] for m in r.nodes
                                      if m["id"] == n["parent"]) + 1


def test_compare_returns_all_algorithms():
    results = compare(EASY, GOAL, ["bfs", "dfs", "ucs"])
    assert [r.algorithm for r in results] == ["bfs", "dfs", "ucs"]
    assert all(r.solved for r in results)


def test_compare_deduplicates_and_validates():
    results = compare(EASY, GOAL, ["bfs", "BFS"])
    assert len(results) == 1
    with pytest.raises(ValueError):
        compare(EASY, GOAL, ["dijkstra"])


def test_limits_validation():
    with pytest.raises(ValueError):
        SearchLimits.from_dict({"max_expanded": 0})
    with pytest.raises(ValueError):
        SearchLimits.from_dict({"max_depth": -1})
    with pytest.raises(ValueError):
        SearchLimits.from_dict({"max_trace": "many"})


def test_dfs_depth_limit():
    limits = SearchLimits(max_expanded=200_000, max_depth=2, max_trace=100)
    r = solve(EASY, GOAL, "dfs", limits)
    # Depth 2 cannot reach a 4-move solution; DFS must fail cleanly.
    assert not r.solved
    assert r.reason in ("exhausted", "limit_exceeded")
    assert r.stats["max_depth"] <= 2


def test_parse_board_used_by_algorithms():
    assert parse_board(list(EASY)) == EASY
