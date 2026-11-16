import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app  # noqa: E402

STUDENT = {"name": "Alice Kumar", "email": "alice@college.edu", "course": "CSE", "year": 2}


@pytest.fixture()
def client(tmp_path):
    app = create_app(str(tmp_path / "test.db"))
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"


def test_student_list_starts_empty(client):
    response = client.get("/students")
    assert response.status_code == 200
    assert response.get_json() == []


def test_create_and_read_student(client):
    created = client.post("/students", json=STUDENT)
    assert created.status_code == 201
    student_id = created.get_json()["id"]

    fetched = client.get(f"/students/{student_id}")
    assert fetched.status_code == 200
    assert fetched.get_json()["name"] == "Alice Kumar"


def test_update_student(client):
    student_id = client.post("/students", json=STUDENT).get_json()["id"]
    updated = client.put(
        f"/students/{student_id}",
        json={"name": "Alice K", "email": "alice.k@college.edu", "course": "CSE", "year": 3},
    )
    assert updated.status_code == 200
    assert client.get(f"/students/{student_id}").get_json()["year"] == 3


def test_delete_student(client):
    student_id = client.post("/students", json=STUDENT).get_json()["id"]
    assert client.delete(f"/students/{student_id}").status_code == 200
    assert client.get(f"/students/{student_id}").status_code == 404


def test_missing_field_rejected(client):
    payload = dict(STUDENT)
    del payload["name"]
    assert client.post("/students", json=payload).status_code == 400


def test_invalid_year_rejected(client):
    payload = dict(STUDENT, year=99)
    assert client.post("/students", json=payload).status_code == 400


def test_duplicate_email_rejected(client):
    assert client.post("/students", json=STUDENT).status_code == 201
    assert client.post("/students", json=STUDENT).status_code == 409


def test_unknown_student_returns_404(client):
    assert client.get("/students/9999").status_code == 404
