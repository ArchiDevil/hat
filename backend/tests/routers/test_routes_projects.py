from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.projects.query import ProjectQuery
from app.projects.schema import ProjectCreate
from main import app


def test_create_project(user_logged_client: TestClient, session: Session):
    """POST /projects/"""
    expected_name = "Test Project"
    path = app.url_path_for("create_project")

    response = user_logged_client.post(url=path, json={"name": expected_name})
    response_json = response.json()

    assert response.status_code == status.HTTP_201_CREATED
    assert response_json["name"] == expected_name
    assert response_json["user_id"] == 1
    assert "id" in response_json
    assert "created_at" in response_json
    assert "updated_at" in response_json
    assert response_json["user"]["id"] == 1


def test_create_project_validation_error(user_logged_client: TestClient):
    """POST /projects/ - validation error for empty name"""
    path = app.url_path_for("create_project")

    response = user_logged_client.post(url=path, json={"name": ""})

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_list_projects(user_logged_client: TestClient, session: Session):
    """GET /projects/"""
    path = app.url_path_for("list_projects")

    project_1 = ProjectQuery(session).create_project(
        user_id=1, data=ProjectCreate(name="Project 1")
    )
    project_2 = ProjectQuery(session).create_project(
        user_id=1, data=ProjectCreate(name="Project 2")
    )

    response = user_logged_client.get(path)
    response_json = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert len(response_json) == 2
    assert response_json[0]["name"] == project_1.name
    assert response_json[1]["name"] == project_2.name


def test_retrieve_project(user_logged_client: TestClient, session: Session):
    """GET /projects/{project_id}/"""
    project = ProjectQuery(session).create_project(
        user_id=1, data=ProjectCreate(name="Test Project")
    )
    path = app.url_path_for("retrieve_project", **{"project_id": project.id})

    response = user_logged_client.get(path)
    response_json = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_json["id"] == project.id
    assert response_json["name"] == project.name
    assert response_json["user_id"] == 1
    assert response_json["user"]["id"] == 1


def test_retrieve_project_unauthorized(fastapi_client: TestClient, session: Session):
    """GET /projects/{project_id}/ - 403 for accessing another user's project"""
    project = ProjectQuery(session).create_project(
        user_id=2, data=ProjectCreate(name="User 2 Project")
    )
    path = app.url_path_for("retrieve_project", **{"project_id": project.id})
    response = fastapi_client.get(path)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_retrieve_project_not_found(user_logged_client: TestClient):
    """GET /projects/{project_id}/ - 404 for non-existent project"""
    response = user_logged_client.get("/projects/999")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Project with id 999 not found"


def test_update_project(user_logged_client: TestClient, session: Session):
    """PUT /projects/{project_id}/"""
    project = ProjectQuery(session).create_project(
        user_id=1, data=ProjectCreate(name="Original Name")
    )
    expected_name = "Updated Name"
    old_time = project.updated_at
    path = app.url_path_for("update_project", **{"project_id": project.id})

    response = user_logged_client.put(url=path, json={"name": expected_name})
    response_json = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_json["name"] == expected_name
    assert response_json["updated_at"] != old_time.isoformat()


def test_update_project_unauthorized(fastapi_client: TestClient, session: Session):
    """PUT /projects/{project_id}/ - 403 for updating another user's project"""
    project = ProjectQuery(session).create_project(
        user_id=2, data=ProjectCreate(name="User 2 Project")
    )
    path = app.url_path_for("update_project", **{"project_id": project.id})

    response = fastapi_client.put(url=path, json={"name": "Updated Name"})

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_update_project_not_found(user_logged_client: TestClient):
    """PUT /projects/{project_id}/ - 404 for non-existent project"""
    response = user_logged_client.put("/projects/999", json={"name": "Updated Name"})

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Project with id 999 not found"


def test_delete_project(user_logged_client: TestClient, session: Session):
    """DELETE /projects/{project_id}/"""
    project = ProjectQuery(session).create_project(
        user_id=1, data=ProjectCreate(name="Test Project")
    )
    path = app.url_path_for("delete_project", **{"project_id": project.id})

    response = user_logged_client.delete(url=path)
    response_json = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_json == {"message": "Deleted"}


def test_delete_project_unauthorized(fastapi_client: TestClient, session: Session):
    """DELETE /projects/{project_id}/ - 403 for deleting another user's project"""
    project = ProjectQuery(session).create_project(
        user_id=2, data=ProjectCreate(name="User 2 Project")
    )
    path = app.url_path_for("delete_project", **{"project_id": project.id})

    response = fastapi_client.delete(url=path)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_delete_project_not_found(user_logged_client: TestClient):
    """DELETE /projects/{project_id}/ - 404 for non-existent project"""
    response = user_logged_client.delete("/projects/999")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Project with id 999 not found"
