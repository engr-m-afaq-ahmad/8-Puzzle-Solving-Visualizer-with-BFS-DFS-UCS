"""Unit tests for puzzle state logic and solvability."""

import pytest

from backend.puzzle import (
    PuzzleError,
    inversions,
    is_solvable,
    manhattan,
    moves_between,
    neighbors,
    parse_board,
)

GOAL = (1, 2, 3, 4, 5, 6, 7, 8, 0)
# Classic solvable board; optimal solution length is 4.
EASY = (1, 2, 3, 4, 0, 6, 7, 5, 8)
# One swap away from goal => unsolvable for standard goal.
UNSOLVABLE = (1, 2, 3, 4, 5, 6, 8, 7, 0)


def test_parse_board_valid():
    assert parse_board([1, 2, 3, 4, 5, 6, 7, 8, 0]) == GOAL


@pytest.mark.parametrize("bad", [
    [1, 2, 3, 4, 5, 6, 7, 8],            # not square
    [1, 2, 3, 4, 5, 6, 7, 8, 9],         # missing blank
    [0, 1, 2, 3, 4, 5, 6, 7, 7],         # duplicate
    [1, 2, 3, 4, 5, 6, 7, 8, "0"],       # non-int
    "123456780",                          # not a list
])
def test_parse_board_invalid(bad):
    with pytest.raises(PuzzleError):
        parse_board(bad)


def test_inversions():
    assert inversions(GOAL) == 0
    assert inversions(UNSOLVABLE) == 1


def test_solvable_standard():
    assert is_solvable(EASY, GOAL)
    assert not is_solvable(UNSOLVABLE, GOAL)


def test_already_solved_is_solvable():
    assert is_solvable(GOAL, GOAL)


def test_arbitrary_goal_parity():
    # Goal with one transposition (odd inversions): a board that is odd
    # relative to the standard goal becomes solvable against this goal.
    goal2 = (1, 2, 3, 4, 5, 6, 8, 7, 0)   # 1 inversion
    start = (1, 2, 3, 4, 5, 6, 7, 8, 0)   # 0 inversions
    assert not is_solvable(start, goal2)
    assert is_solvable(UNSOLVABLE, goal2)


def test_size_mismatch_raises():
    with pytest.raises(PuzzleError):
        is_solvable((1, 2, 3, 0), GOAL)


def test_neighbors_corner_has_two_moves():
    n = neighbors(GOAL)  # blank at bottom-right corner
    assert len(n) == 2
    moves = {mv for _, mv in n}
    assert moves == {"Up", "Left"}


def test_neighbors_center_has_four_moves():
    center = (1, 2, 3, 4, 0, 6, 7, 8, 5)
    assert len(neighbors(center)) == 4


def test_neighbors_are_inverse():
    # Every neighbor is exactly one legal move from its parent and the
    # reverse move gets back.
    state = EASY
    back = {"Up": "Down", "Down": "Up", "Left": "Right", "Right": "Left"}
    for succ, mv in neighbors(state):
        assert (state, back[mv]) in neighbors(succ)
        assert moves_between(state, succ) == mv


def test_manhattan():
    assert manhattan(GOAL, GOAL) == 0
    # Tile 8 is one step away from its goal cell.
    assert manhattan(EASY, GOAL) == 2
