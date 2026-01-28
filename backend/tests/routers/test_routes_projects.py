from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.documents.models import Document, DocumentRecord, DocumentType
from app.projects.models import Project
from app.projects.query import ProjectQuery
from app.projects.schema import ProjectCreate
from main import app


def test_create_project(user_logged_client: TestClient, session: Session):
    expected_name = "Test Project"
    path = app.url_path_for("create_project")

    response = user_logged_client.post(url=path, json={"name": expected_name})
    response_json = response.json()

    assert response.status_code == status.HTTP_201_CREATED
    assert response_json["name"] == expected_name
    assert response_json["created_by"] == 1
    assert "id" in response_json
    assert "created_at" in response_json
    assert "updated_at" in response_json


def test_create_project_validation_error(user_logged_client: TestClient):
    path = app.url_path_for("create_project")

    response = user_logged_client.post(url=path, json={"name": ""})

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_list_projects(user_logged_client: TestClient, session: Session):
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
    assert len(response_json) == 3
    assert response_json[0]["name"] == "Unnamed project"
    assert response_json[1]["name"] == project_1.name
    assert response_json[2]["name"] == project_2.name


def test_retrieve_project(user_logged_client: TestClient, session: Session):
    project = ProjectQuery(session).create_project(
        user_id=1, data=ProjectCreate(name="Test Project")
    )
    path = app.url_path_for("retrieve_project", **{"project_id": project.id})

    response = user_logged_client.get(path)
    response_json = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_json["id"] == project.id
    assert response_json["name"] == project.name
    assert response_json["created_by"] == 1


def test_retrieve_project_unauthorized(fastapi_client: TestClient, session: Session):
    project = ProjectQuery(session).create_project(
        user_id=2, data=ProjectCreate(name="User 2 Project")
    )
    path = app.url_path_for("retrieve_project", **{"project_id": project.id})
    response = fastapi_client.get(path)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_retrieve_project_not_found(user_logged_client: TestClient):
    response = user_logged_client.get("/projects/999")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Project with id 999 not found"


def test_update_project(user_logged_client: TestClient, session: Session):
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
    project = ProjectQuery(session).create_project(
        user_id=2, data=ProjectCreate(name="User 2 Project")
    )
    path = app.url_path_for("update_project", **{"project_id": project.id})

    response = fastapi_client.put(url=path, json={"name": "Updated Name"})

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_update_project_not_found(user_logged_client: TestClient):
    response = user_logged_client.put("/projects/999", json={"name": "Updated Name"})

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Project with id 999 not found"


def test_delete_project(user_logged_client: TestClient, session: Session):
    project = ProjectQuery(session).create_project(
        user_id=1, data=ProjectCreate(name="Test Project")
    )
    path = app.url_path_for("delete_project", **{"project_id": project.id})

    response = user_logged_client.delete(url=path)
    response_json = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_json == {"message": "Deleted"}


def test_delete_project_unauthorized(fastapi_client: TestClient, session: Session):
    project = ProjectQuery(session).create_project(
        user_id=2, data=ProjectCreate(name="User 2 Project")
    )
    path = app.url_path_for("delete_project", **{"project_id": project.id})

    response = fastapi_client.delete(url=path)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_delete_project_not_found(user_logged_client: TestClient):
    response = user_logged_client.delete("/projects/999")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Project with id 999 not found"


def test_retrieve_project_with_aggregates(
    user_logged_client: TestClient, session: Session
):
    with session as s:
        project = Project(created_by=1, name="Test Project")
        s.add(project)
        s.flush()
        project_id = project.id

        doc = Document(
            name="doc.txt",
            type=DocumentType.txt,
            processing_status="done",
            created_by=1,
            project_id=project_id,
            records=[
                DocumentRecord(
                    source="Hello", target="Привет", approved=True, word_count=1
                ),
                DocumentRecord(
                    source="World", target="Мир", approved=False, word_count=1
                ),
                DocumentRecord(
                    source="Test", target="Тест", approved=True, word_count=2
                ),
            ],
        )
        s.add(doc)
        s.commit()

    response = user_logged_client.get(f"/projects/{project_id}")
    assert response.status_code == status.HTTP_200_OK
    response_json = response.json()

    assert response_json["id"] == project_id
    assert response_json["name"] == "Test Project"
    # 2 approved records (Hello, Test)
    assert response_json["approved_records_count"] == 2
    # 3 total records (Hello, World, Test)
    assert response_json["total_records_count"] == 3
    # 3 approved words (1 + 2)
    assert response_json["approved_words_count"] == 3
    # 4 total words (1 + 1 + 2)
    assert response_json["total_words_count"] == 4
    assert len(response_json["documents"]) == 1


def test_retrieve_project_empty(user_logged_client: TestClient, session: Session):
    with session as s:
        project = Project(created_by=1, name="Empty Project")
        s.add(project)
        s.commit()
        project_id = project.id

    response = user_logged_client.get(f"/projects/{project_id}")
    assert response.status_code == status.HTTP_200_OK
    response_json = response.json()

    assert response_json["id"] == project_id
    assert response_json["name"] == "Empty Project"
    assert response_json["approved_records_count"] == 0
    assert response_json["total_records_count"] == 0
    assert response_json["approved_words_count"] == 0
    assert response_json["total_words_count"] == 0


def test_retrieve_project_project_with_documents_no_records(
    user_logged_client: TestClient, session: Session
):
    with session as s:
        project = Project(created_by=1, name="Project with Empty Docs")
        s.add(project)
        s.flush()

        doc = Document(
            name="empty_doc.txt",
            type=DocumentType.txt,
            processing_status="done",
            created_by=1,
            project_id=project.id,
        )
        s.add(doc)
        s.commit()

    response = user_logged_client.get("/projects/1")
    assert response.status_code == status.HTTP_200_OK

    project_data = response.json()
    assert project_data["name"] == "Project with Empty Docs"
    assert project_data["approved_records_count"] == 0
    assert project_data["total_records_count"] == 0
    assert project_data["approved_words_count"] == 0
    assert project_data["total_words_count"] == 0


def test_retrieve_unnamed_project(user_logged_client: TestClient, session: Session):
    with session as s:
        project = Project(created_by=1, name="Test Project")
        s.add(project)
        s.flush()
        project_id = project.id

        doc1 = Document(
            name="doc.txt",
            type=DocumentType.txt,
            processing_status="done",
            created_by=1,
            project_id=project_id,
            records=[
                DocumentRecord(
                    source="Hello", target="Привет", approved=True, word_count=10
                ),
                DocumentRecord(
                    source="World", target="Мир", approved=False, word_count=10
                ),
                DocumentRecord(
                    source="Test", target="Тест", approved=True, word_count=20
                ),
            ],
        )
        doc2 = Document(
            name="doc.txt",
            type=DocumentType.txt,
            processing_status="done",
            created_by=1,
            project_id=None,
            records=[
                DocumentRecord(
                    source="Hello", target="Привет", approved=True, word_count=1
                ),
                DocumentRecord(
                    source="World", target="Мир", approved=False, word_count=1
                ),
                DocumentRecord(
                    source="Test", target="Тест", approved=True, word_count=2
                ),
            ],
        )

        s.add(doc1)
        s.add(doc2)
        s.commit()

    response = user_logged_client.get("/projects/-1")
    assert response.status_code == status.HTTP_200_OK
    response_json = response.json()

    assert response_json["id"] == -1
    assert response_json["name"] == "Unnamed project"
    # 2 approved records (Hello, Test)
    assert response_json["approved_records_count"] == 2
    # 3 total records (Hello, World, Test)
    assert response_json["total_records_count"] == 3
    # 3 approved words (1 + 2)
    assert response_json["approved_words_count"] == 3
    # 4 total words (1 + 1 + 2)
    assert response_json["total_words_count"] == 4
    assert len(response_json["documents"]) == 1
    assert response_json["documents"][0]["id"] == 2
