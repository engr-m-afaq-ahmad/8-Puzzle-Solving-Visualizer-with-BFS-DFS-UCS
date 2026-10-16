"""End-to-end API tests via the Flask test client."""

import pytest

from backend import create_app

GOAL = [1, 2, 3, 4, 5, 6, 7, 8, 0]
EASY = [1, 2, 3, 4, 0, 6, 7, 5, 8]
UNSOLVABLE = [1, 2, 3, 4, 5, 6, 8, 7, 0]


@pytest.fixture()
def client():
    app = create_app({"TESTING": True})
    with app.test_client() as c:
        yield c


def test_health(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "ok"
    assert set(data["algorithms"]) == {"bfs", "dfs", "ucs"}


def test_solve_default_goal(client):
    res = client.post("/api/solve",
                      json={"board": EASY, "algorithm": "bfs"})
    assert res.status_code == 200
    data = res.get_json()
    assert data["solved"] is True
    assert data["goal"] == GOAL
    assert data["solution"]["path"][0] == EASY
    assert data["solution"]["path"][-1] == GOAL
    assert data["solution"]["length"] == 4
    assert data["stats"]["nodes_expanded"] > 0
    assert data["events"] and data["nodes"]


def test_solve_all_algorithms(client):
    for algo in ("bfs", "dfs", "ucs"):
        res = client.post("/api/solve",
                          json={"board": EASY, "algorithm": algo})
        assert res.status_code == 200
        assert res.get_json()["solved"] is True


def test_solve_unsolvable(client):
    res = client.post("/api/solve",
                      json={"board": UNSOLVABLE, "algorithm": "bfs"})
    assert res.status_code == 200
    data = res.get_json()
    assert data["solvable"] is False
    assert data["solved"] is False
    assert data["reason"] == "unsolvable"
    assert data["solution"]["path"] == []


def test_solve_invalid_algorithm(client):
    res = client.post("/api/solve",
                      json={"board": EASY, "algorithm": "magic"})
    assert res.status_code == 400
    assert "error" in res.get_json()


def test_solve_invalid_board(client):
    res = client.post("/api/solve", json={"board": [1, 2, 3]})
    assert res.status_code == 400
    res = client.post("/api/solve", json={"board": [1, 1, 2, 3, 4, 5, 6, 7, 8]})
    assert res.status_code == 400
    res = client.post("/api/solve", json={})
    assert res.status_code == 400


def test_solve_invalid_json(client):
    res = client.post("/api/solve", data="not json",
                      content_type="application/json")
    assert res.status_code == 400


def test_solve_invalid_limits(client):
    res = client.post("/api/solve",
                      json={"board": EASY, "limits": {"max_expanded": 0}})
    assert res.status_code == 400


def test_solve_custom_goal(client):
    goal = [1, 2, 3, 4, 5, 6, 8, 7, 0]
    start = [1, 2, 3, 4, 5, 6, 0, 8, 7]
    res = client.post("/api/solve",
                      json={"board": start, "goal": goal, "algorithm": "bfs"})
    assert res.status_code == 200
    data = res.get_json()
    assert data["solved"] is True
    assert data["solution"]["path"][-1] == goal
    assert data["solution"]["length"] == 1


def test_solve_size_mismatch(client):
    res = client.post("/api/solve",
                      json={"board": EASY, "goal": [1, 2, 3, 0]})
    assert res.status_code == 400


def test_validate(client):
    res = client.post("/api/validate", json={"board": EASY})
    assert res.status_code == 200
    data = res.get_json()
    assert data["solvable"] is True
    assert data["already_solved"] is False

    res = client.post("/api/validate", json={"board": UNSOLVABLE})
    assert res.get_json()["solvable"] is False

    res = client.post("/api/validate", json={"board": GOAL})
    assert res.get_json()["already_solved"] is True

    res = client.post("/api/validate", json={"board": [1, 2, 3]})
    assert res.status_code == 400


def test_compare(client):
    res = client.post("/api/compare",
                      json={"board": EASY,
                            "algorithms": ["bfs", "dfs", "ucs"]})
    assert res.status_code == 200
    data = res.get_json()
    assert len(data["results"]) == 3
    by_algo = {r["algorithm"]: r for r in data["results"]}
    assert by_algo["bfs"]["solution"]["length"] == 4
    assert by_algo["ucs"]["solution"]["length"] == 4
    assert by_algo["dfs"]["solved"] is True
    assert by_algo["bfs"]["stats"]["nodes_expanded"] != \
        by_algo["dfs"]["stats"]["nodes_expanded"]


def test_compare_unknown_algorithm(client):
    res = client.post("/api/compare",
                      json={"board": EASY, "algorithms": ["nope"]})
    assert res.status_code == 400


def test_unknown_api_route_is_json_404(client):
    res = client.get("/api/nope")
    assert res.status_code == 404
    assert res.get_json()["error"]


def test_method_not_allowed(client):
    res = client.get("/api/solve")
    assert res.status_code == 405


def test_health_wrong_method(client):
    assert client.post("/api/health").status_code == 405
