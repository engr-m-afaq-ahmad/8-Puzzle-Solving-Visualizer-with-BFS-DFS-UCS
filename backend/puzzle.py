"""Core 8-puzzle / N-puzzle state logic: validation, solvability, neighbors.

States are represented as tuples of ints of length width*height. The blank
tile is always ``0``. Using tuples keeps states hashable for visited-sets.
"""

from __future__ import annotations

from typing import List, Sequence, Tuple

State = Tuple[int, ...]

# Blank movement directions. A "move" is the direction the blank travels.
MOVES: Tuple[str, ...] = ("Up", "Down", "Left", "Right")
_DELTA = {"Up": (-1, 0), "Down": (1, 0), "Left": (0, -1), "Right": (0, 1)}

BLANK = 0


class PuzzleError(ValueError):
    """Raised for malformed boards / goals."""


def parse_board(raw: Sequence, *, label: str = "board") -> State:
    """Validate and normalise a raw JSON list into a State tuple.

    Accepts a flat list of ``width*height`` unique integers containing
    exactly one blank (0). Defaults to 3x3 but the size is inferred from
    the square length of the input.
    """
    if not isinstance(raw, (list, tuple)):
        raise PuzzleError(f"'{label}' must be an array of integers")
    tiles = list(raw)
    n = len(tiles)
    side = int(round(n ** 0.5))
    if side * side != n or side < 2:
        raise PuzzleError(f"'{label}' must be a square-sized array (e.g. 9 for 3x3)")
    for t in tiles:
        if not isinstance(t, int) or isinstance(t, bool):
            raise PuzzleError(f"'{label}' must contain only integers")
    if sorted(tiles) != list(range(n)):
        raise PuzzleError(
            f"'{label}' must contain each value 0..{n - 1} exactly once"
        )
    return tuple(tiles)


def width(state: State) -> int:
    return int(round(len(state) ** 0.5))


def inversions(state: State) -> int:
    """Number of tile-pair inversions, ignoring the blank."""
    seq = [t for t in state if t != BLANK]
    return sum(
        1
        for i in range(len(seq))
        for j in range(i + 1, len(seq))
        if seq[i] > seq[j]
    )


def blank_index(state: State) -> int:
    return state.index(BLANK)


def _row_from_bottom(state: State, index: int) -> int:
    w = width(state)
    return w - (index // w)


def is_solvable(start: State, goal: State) -> bool:
    """Parity-based solvability test for an arbitrary goal permutation.

    Odd-width boards: solvable iff both boards have the same inversion
    parity. Even-width boards also factor in the blank's row from the
    bottom (standard 15-puzzle criterion).
    """
    if len(start) != len(goal):
        raise PuzzleError("start and goal must be the same size")
    if sorted(start) != sorted(goal):
        raise PuzzleError("start and goal must contain the same tiles")
    w = width(start)
    if w % 2 == 1:
        return inversions(start) % 2 == inversions(goal) % 2
    parity_s = (inversions(start) + _row_from_bottom(start, blank_index(start))) % 2
    parity_g = (inversions(goal) + _row_from_bottom(goal, blank_index(goal))) % 2
    return parity_s == parity_g


def neighbors(state: State) -> List[Tuple[State, str]]:
    """All legal successor states paired with the move that produced them.

    Moves are ordered Up, Down, Left, Right (direction the blank travels)
    which gives deterministic, reproducible exploration order.
    """
    w = width(state)
    b = blank_index(state)
    r, c = divmod(b, w)
    out: List[Tuple[State, str]] = []
    for mv in MOVES:
        dr, dc = _DELTA[mv]
        nr, nc = r + dr, c + dc
        if 0 <= nr < w and 0 <= nc < w:
            nb = nr * w + nc
            tiles = list(state)
            tiles[b], tiles[nb] = tiles[nb], tiles[b]
            out.append((tuple(tiles), mv))
    return out


def manhattan(state: State, goal: State) -> int:
    """Sum of Manhattan distances of every tile from its goal cell."""
    w = width(state)
    goal_pos = {t: i for i, t in enumerate(goal)}
    total = 0
    for i, t in enumerate(state):
        if t == BLANK:
            continue
        gi = goal_pos[t]
        total += abs(i // w - gi // w) + abs(i % w - gi % w)
    return total


def to_rows(state: State) -> List[List[int]]:
    w = width(state)
    return [list(state[i * w:(i + 1) * w]) for i in range(w)]


def moves_between(a: State, b: State) -> str:
    """Label describing the blank movement from state ``a`` to ``b``."""
    w = width(a)
    ai, bi = blank_index(a), blank_index(b)
    ar, ac = divmod(ai, w)
    br, bc = divmod(bi, w)
    dr, dc = br - ar, bc - ac
    for mv, (mr, mc) in _DELTA.items():
        if (mr, mc) == (dr, dc):
            return mv
    raise PuzzleError("states are not adjacent")
