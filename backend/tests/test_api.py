import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.session import Base, get_db
from app.main import app

# Use an in-memory SQLite DB for tests so nothing gets written to disk
TEST_DATABASE_URL = "sqlite:///./test_taskmanager.db"

engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def registered_user(client):
    client.post("/register", json={"username": "alice", "email": "alice@example.com", "password": "secret123"})
    return {"username": "alice", "password": "secret123"}


@pytest.fixture
def auth_headers(client, registered_user):
    resp = client.post("/login", json=registered_user)
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ── Auth tests ──────────────────────────────────────────────────────────────


def test_register_success(client):
    resp = client.post(
        "/register",
        json={"username": "bob", "email": "bob@example.com", "password": "password1"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["username"] == "bob"
    assert "id" in data


def test_register_duplicate_username(client, registered_user):
    resp = client.post(
        "/register",
        json={"username": "alice", "email": "other@example.com", "password": "password1"},
    )
    assert resp.status_code == 409


def test_register_duplicate_email(client, registered_user):
    resp = client.post(
        "/register",
        json={"username": "alice2", "email": "alice@example.com", "password": "password1"},
    )
    assert resp.status_code == 409


def test_login_success(client, registered_user):
    resp = client.post("/login", json=registered_user)
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_login_wrong_password(client, registered_user):
    resp = client.post("/login", json={"username": "alice", "password": "wrong"})
    assert resp.status_code == 401


# ── Task tests ──────────────────────────────────────────────────────────────


def test_create_task(client, auth_headers):
    resp = client.post("/tasks", json={"title": "Buy milk"}, headers=auth_headers)
    assert resp.status_code == 201
    assert resp.json()["title"] == "Buy milk"
    assert resp.json()["completed"] is False


def test_list_tasks_empty(client, auth_headers):
    resp = client.get("/tasks", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["total"] == 0


def test_list_tasks_pagination(client, auth_headers):
    for i in range(5):
        client.post("/tasks", json={"title": f"Task {i}"}, headers=auth_headers)
    resp = client.get("/tasks?page=1&page_size=3", headers=auth_headers)
    assert resp.json()["total"] == 5
    assert len(resp.json()["tasks"]) == 3


def test_filter_completed(client, auth_headers):
    r1 = client.post("/tasks", json={"title": "Done task"}, headers=auth_headers)
    client.post("/tasks", json={"title": "Pending task"}, headers=auth_headers)
    task_id = r1.json()["id"]
    client.put(f"/tasks/{task_id}", json={"completed": True}, headers=auth_headers)

    resp = client.get("/tasks?completed=true", headers=auth_headers)
    assert resp.json()["total"] == 1

    resp2 = client.get("/tasks?completed=false", headers=auth_headers)
    assert resp2.json()["total"] == 1


def test_get_task(client, auth_headers):
    create_resp = client.post("/tasks", json={"title": "Check me"}, headers=auth_headers)
    task_id = create_resp.json()["id"]
    resp = client.get(f"/tasks/{task_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == task_id


def test_get_task_not_found(client, auth_headers):
    resp = client.get("/tasks/9999", headers=auth_headers)
    assert resp.status_code == 404


def test_update_task(client, auth_headers):
    create_resp = client.post("/tasks", json={"title": "Old title"}, headers=auth_headers)
    task_id = create_resp.json()["id"]
    resp = client.put(f"/tasks/{task_id}", json={"title": "New title", "completed": True}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["title"] == "New title"
    assert resp.json()["completed"] is True


def test_delete_task(client, auth_headers):
    create_resp = client.post("/tasks", json={"title": "Delete me"}, headers=auth_headers)
    task_id = create_resp.json()["id"]
    resp = client.delete(f"/tasks/{task_id}", headers=auth_headers)
    assert resp.status_code == 204
    assert client.get(f"/tasks/{task_id}", headers=auth_headers).status_code == 404


def test_user_cannot_access_other_user_task(client):
    # Register two users
    client.post("/register", json={"username": "user1", "email": "u1@example.com", "password": "pass123"})
    client.post("/register", json={"username": "user2", "email": "u2@example.com", "password": "pass123"})

    token1 = client.post("/login", json={"username": "user1", "password": "pass123"}).json()["access_token"]
    token2 = client.post("/login", json={"username": "user2", "password": "pass123"}).json()["access_token"]

    headers1 = {"Authorization": f"Bearer {token1}"}
    headers2 = {"Authorization": f"Bearer {token2}"}

    task_id = client.post("/tasks", json={"title": "Private"}, headers=headers1).json()["id"]

    # user2 should not be able to read or delete user1's task
    assert client.get(f"/tasks/{task_id}", headers=headers2).status_code == 404
    assert client.delete(f"/tasks/{task_id}", headers=headers2).status_code == 404


def test_unauthenticated_request(client):
    resp = client.get("/tasks")
    assert resp.status_code == 401
