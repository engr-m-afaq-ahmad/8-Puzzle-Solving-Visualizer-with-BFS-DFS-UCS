"""Flask application: API routes + production static/SPA serving.

Development: ``app.run()`` on :5000, with Vite proxying ``/api`` here.
Production:  ``run.py`` serves the built React bundle from
``backend/static`` on the same origin/port — no Node server required.
"""

from __future__ import annotations

import os
from typing import Tuple

from flask import Flask, jsonify, request, send_from_directory

from .algorithms import ALGORITHMS, DEFAULT_LIMITS, SearchLimits, compare, solve
from .puzzle import PuzzleError, inversions, is_solvable, parse_board, width

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")


def _extract_boards(payload: dict) -> Tuple[tuple, tuple]:
    if not isinstance(payload, dict):
        raise PuzzleError("request body must be a JSON object")
    if "board" not in payload:
        raise PuzzleError("'board' is required")
    goal = payload.get("goal")
    if goal is None:
        # Default goal: tiles 1..8 in order, blank last.
        n = len(payload["board"]) if isinstance(payload["board"], (list, tuple)) else 9
        side = int(round(n ** 0.5)) if n else 3
        goal = [i for i in range(1, side * side)] + [0]
    start = parse_board(payload["board"], label="board")
    goal = parse_board(goal, label="goal")
    if len(start) != len(goal):
        raise PuzzleError("'board' and 'goal' must be the same size")
    return start, goal


def create_app(config: dict | None = None) -> Flask:
    app = Flask(__name__, static_folder=None)
    app.config.setdefault("JSON_SORT_KEYS", False)
    if config:
        app.config.update(config)

    def error(message: str, status: int):
        return jsonify({"error": message}), status

    # ---------------------------------------------------------------- health
    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok", "service": "8-puzzle-api",
                        "algorithms": list(ALGORITHMS),
                        "default_limits": dict(DEFAULT_LIMITS)})

    # -------------------------------------------------------------- validate
    @app.post("/api/validate")
    def validate():
        try:
            payload = request.get_json(silent=True)
            if payload is None:
                return error("request body must be valid JSON", 400)
            start, goal = _extract_boards(payload)
        except PuzzleError as exc:
            return error(str(exc), 400)
        solvable = is_solvable(start, goal)
        return jsonify({
            "valid": True,
            "solvable": solvable,
            "board": list(start),
            "goal": list(goal),
            "inversions_board": inversions(start),
            "inversions_goal": inversions(goal),
            "size": width(start),
            "already_solved": start == goal,
        })

    # ----------------------------------------------------------------- solve
    @app.post("/api/solve")
    def solve_route():
        try:
            payload = request.get_json(silent=True)
            if payload is None:
                return error("request body must be valid JSON", 400)
            start, goal = _extract_boards(payload)
            algorithm = (payload.get("algorithm") or "bfs").lower()
            if algorithm not in ALGORITHMS:
                return error(f"algorithm must be one of {', '.join(ALGORITHMS)}", 400)
            limits = SearchLimits.from_dict(payload.get("limits"))
        except PuzzleError as exc:
            return error(str(exc), 400)
        except ValueError as exc:
            return error(str(exc), 400)
        result = solve(start, goal, algorithm, limits)
        return jsonify(result.to_dict())

    # --------------------------------------------------------------- compare
    @app.post("/api/compare")
    def compare_route():
        try:
            payload = request.get_json(silent=True)
            if payload is None:
                return error("request body must be valid JSON", 400)
            start, goal = _extract_boards(payload)
            algorithms = payload.get("algorithms") or list(ALGORITHMS)
            if not isinstance(algorithms, list) or not algorithms:
                return error("'algorithms' must be a non-empty array", 400)
            limits = SearchLimits.from_dict(payload.get("limits"))
            results = compare(start, goal, algorithms, limits)
        except PuzzleError as exc:
            return error(str(exc), 400)
        except ValueError as exc:
            return error(str(exc), 400)
        return jsonify({
            "board": list(start),
            "goal": list(goal),
            "results": [r.to_dict() for r in results],
        })

    # ------------------------------------------- production static + SPA
    @app.get("/")
    def spa_index():
        return send_from_directory(STATIC_DIR, "index.html")

    @app.get("/<path:path>")
    def spa_catch_all(path: str):
        # Unknown /api routes must 404 as JSON, never fall through to HTML.
        if path.startswith("api/"):
            return error(f"unknown endpoint: /{path}", 404)
        full = os.path.join(STATIC_DIR, path)
        if os.path.isfile(full):
            return send_from_directory(STATIC_DIR, path)
        # SPA client-side route fallback.
        index = os.path.join(STATIC_DIR, "index.html")
        if os.path.isfile(index):
            return send_from_directory(STATIC_DIR, "index.html")
        return error(
            "frontend build not found. Run `npm run build` inside frontend/ "
            "before starting the production server.", 404)

    @app.errorhandler(404)
    def not_found(_e):
        return error("not found", 404)

    @app.errorhandler(405)
    def method_not_allowed(_e):
        return error("method not allowed", 405)

    @app.errorhandler(500)
    def server_error(_e):
        return error("internal server error", 500)

    return app
