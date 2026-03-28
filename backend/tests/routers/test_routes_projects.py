from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.documents.models import Document, DocumentRecord, DocumentType
from app.glossary.models import Glossary, ProcessingStatuses
from app.glossary.query import GlossaryQuery
from app.glossary.schema import GlossaryRecordCreate
from app.projects.models import (
    Project,
    ProjectGlossaryAssociation,
    ProjectTmAssociation,
)
from app.projects.query import ProjectQuery
from app.projects.schema import ProjectCreate
from app.translation_memory.models import TranslationMemory
from main import app


def test_create_project(admin_logged_client: TestClient, session: Session):
    expected_name = "Test Project"
    path = app.url_path_for("create_project")

    response = admin_logged_client.post(url=path, json={"name": expected_name})
    response_json = response.json()

    assert response.status_code == status.HTTP_201_CREATED
    assert response_json["name"] == expected_name
    assert response_json["created_by"] == 2
    assert "id" in response_json
    assert "created_at" in response_json
    assert "updated_at" in response_json


def test_create_project_validation_error(admin_logged_client: TestClient):
    path = app.url_path_for("create_project")
    response = admin_logged_client.post(url=path, json={"name": ""})
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
    assert len(response_json) == 2
    assert response_json[0]["name"] == project_1.name
    assert response_json[1]["name"] == project_2.name


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


def test_update_project(admin_logged_client: TestClient, session: Session):
    project = ProjectQuery(session).create_project(
        user_id=1, data=ProjectCreate(name="Original Name")
    )
    expected_name = "Updated Name"
    old_time = project.updated_at
    path = app.url_path_for("update_project", **{"project_id": project.id})

    response = admin_logged_client.put(url=path, json={"name": expected_name})
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


def test_update_project_not_found(admin_logged_client: TestClient):
    response = admin_logged_client.put("/projects/999", json={"name": "Updated Name"})

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Project with id 999 not found"


def test_delete_project(admin_logged_client: TestClient, session: Session):
    project = ProjectQuery(session).create_project(
        user_id=1, data=ProjectCreate(name="Test Project")
    )
    path = app.url_path_for("delete_project", **{"project_id": project.id})

    response = admin_logged_client.delete(url=path)
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


def test_delete_project_not_found(admin_logged_client: TestClient):
    response = admin_logged_client.delete("/projects/999")

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


def test_get_project_glossaries(user_logged_client: TestClient, session: Session):
    """Test getting glossaries for a project."""
    with session as s:
        project = Project(created_by=1, name="Test Project")
        s.add(project)
        s.flush()
        project_id = project.id

        glossary = Glossary(
            name="test_glossary",
            created_by=1,
            processing_status=ProcessingStatuses.DONE,
        )
        s.add(glossary)
        s.flush()
        glossary_id = glossary.id

        association = ProjectGlossaryAssociation(
            project_id=project_id, glossary_id=glossary_id
        )
        s.add(association)
        s.commit()

    response = user_logged_client.get(f"/projects/{project_id}/glossaries")
    assert response.status_code == status.HTTP_200_OK
    response_json = response.json()
    assert response_json["glossaries"][0]["id"] == glossary_id
    assert response_json["glossaries"][0]["name"] == "test_glossary"


def test_get_project_glossaries_empty(user_logged_client: TestClient, session: Session):
    """Test getting glossaries for a project with no glossaries."""
    with session as s:
        project = Project(created_by=1, name="Test Project")
        s.add(project)
        s.commit()
        project_id = project.id

    response = user_logged_client.get(f"/projects/{project_id}/glossaries")
    assert response.status_code == status.HTTP_200_OK
    response_json = response.json()
    assert response_json["id"] == 1
    assert response_json["glossaries"] == []


def test_get_project_glossaries_not_found(user_logged_client: TestClient):
    """Test getting glossaries for a non-existent project."""
    response = user_logged_client.get("/projects/999/glossaries")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_set_project_glossaries(admin_logged_client: TestClient, session: Session):
    """Test setting glossaries for a project."""
    with session as s:
        project = Project(created_by=1, name="Test Project")
        s.add(project)
        s.flush()
        project_id = project.id

        glossary = Glossary(
            name="test_glossary",
            created_by=1,
            processing_status=ProcessingStatuses.DONE,
        )
        s.add(glossary)
        s.commit()
        glossary_id = glossary.id

    response = admin_logged_client.post(
        f"/projects/{project_id}/glossaries",
        json={"glossaries": [glossary_id]},
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"message": "Glossary list updated"}

    with session as s:
        associations = s.query(ProjectGlossaryAssociation).all()
        assert len(associations) == 1
        assert associations[0].project_id == project_id
        assert associations[0].glossary_id == glossary_id


def test_set_project_glossaries_multiple(
    admin_logged_client: TestClient, session: Session
):
    """Test setting multiple glossaries for a project."""
    with session as s:
        project = Project(created_by=1, name="Test Project")
        s.add(project)
        s.flush()
        project_id = project.id

        glossary1 = Glossary(
            name="test_glossary1",
            created_by=1,
            processing_status=ProcessingStatuses.DONE,
        )
        glossary2 = Glossary(
            name="test_glossary2",
            created_by=1,
            processing_status=ProcessingStatuses.DONE,
        )
        s.add_all([glossary1, glossary2])
        s.commit()
        glossary1_id = glossary1.id
        glossary2_id = glossary2.id

    response = admin_logged_client.post(
        f"/projects/{project_id}/glossaries",
        json={"glossaries": [glossary1_id, glossary2_id]},
    )
    assert response.status_code == status.HTTP_200_OK

    with session as s:
        associations = s.query(ProjectGlossaryAssociation).all()
        assert len(associations) == 2


def test_set_project_glossaries_replaces_existing(
    admin_logged_client: TestClient, session: Session
):
    """Test that setting glossaries replaces existing ones."""
    with session as s:
        project = Project(created_by=1, name="Test Project")
        s.add(project)
        s.flush()
        project_id = project.id

        glossary1 = Glossary(
            name="test_glossary1",
            created_by=1,
            processing_status=ProcessingStatuses.DONE,
        )
        glossary2 = Glossary(
            name="test_glossary2",
            created_by=1,
            processing_status=ProcessingStatuses.DONE,
        )
        s.add_all([glossary1, glossary2])
        s.flush()
        glossary1_id = glossary1.id
        glossary2_id = glossary2.id

        # Add initial association
        s.add(
            ProjectGlossaryAssociation(project_id=project_id, glossary_id=glossary1_id)
        )
        s.commit()

    # Replace with different glossary
    response = admin_logged_client.post(
        f"/projects/{project_id}/glossaries",
        json={"glossaries": [glossary2_id]},
    )
    assert response.status_code == status.HTTP_200_OK

    with session as s:
        associations = s.query(ProjectGlossaryAssociation).all()
        assert len(associations) == 1
        assert associations[0].glossary_id == glossary2_id


def test_set_project_glossaries_project_not_found(
    admin_logged_client: TestClient, session: Session
):
    """Test setting glossaries for a non-existent project."""
    with session as s:
        glossary = Glossary(
            name="test_glossary",
            created_by=1,
            processing_status=ProcessingStatuses.DONE,
        )
        s.add(glossary)
        s.commit()
        glossary_id = glossary.id

    response = admin_logged_client.post(
        "/projects/999/glossaries",
        json={"glossaries": [glossary_id]},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_set_project_glossaries_glossary_not_found(
    admin_logged_client: TestClient, session: Session
):
    """Test setting non-existent glossaries for a project."""
    with session as s:
        project = Project(created_by=1, name="Test Project")
        s.add(project)
        s.commit()
        project_id = project.id

    response = admin_logged_client.post(
        f"/projects/{project_id}/glossaries",
        json={"glossaries": [999]},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_project_glossary_search_with_matching_records(
    user_logged_client: TestClient, session: Session
):
    """Test searching glossaries for a project with matching records."""
    with session as s:
        project = Project(created_by=1, name="Test Project")
        s.add(project)
        s.flush()
        project_id = project.id

        glossary = Glossary(
            name="test_glossary",
            created_by=1,
            processing_status=ProcessingStatuses.DONE,
        )
        s.add(glossary)
        s.flush()
        glossary_id = glossary.id

        gq = GlossaryQuery(s)
        gq.create_glossary_record(
            1,
            GlossaryRecordCreate(
                comment=None,
                source="Regional Effects",
                target="Региональные эффекты",
            ),
            glossary_id,
        )
        gq.create_glossary_record(
            1,
            GlossaryRecordCreate(
                comment=None,
                source="User Interface",
                target="Пользовательский интерфейс",
            ),
            glossary_id,
        )

        association = ProjectGlossaryAssociation(
            project_id=project_id, glossary_id=glossary_id
        )
        s.add(association)
        s.commit()

    response = user_logged_client.get(
        f"/projects/{project_id}/glossary_search?query=Regional Effects"
    )
    assert response.status_code == status.HTTP_200_OK
    response_json = response.json()
    assert len(response_json) == 1
    assert response_json[0]["source"] == "Regional Effects"
    assert response_json[0]["target"] == "Региональные эффекты"
    assert response_json[0]["glossary_id"] == glossary_id
    assert response_json[0]["comment"] is None
    assert response_json[0]["created_by_user"]["id"] == 1


def test_project_glossary_search_empty_when_no_glossaries(
    user_logged_client: TestClient, session: Session
):
    """Test searching glossaries for a project with no glossaries."""
    with session as s:
        project = Project(created_by=1, name="Test Project")
        s.add(project)
        s.commit()
        project_id = project.id

    response = user_logged_client.get(
        f"/projects/{project_id}/glossary_search?query=Regional Effects"
    )
    assert response.status_code == status.HTTP_200_OK
    response_json = response.json()
    assert response_json == []


def test_project_glossary_search_empty_when_no_matches(
    user_logged_client: TestClient, session: Session
):
    """Test searching glossaries for a project with no matching records."""
    with session as s:
        project = Project(created_by=1, name="Test Project")
        s.add(project)
        s.flush()
        project_id = project.id

        glossary = Glossary(
            name="test_glossary",
            created_by=1,
            processing_status=ProcessingStatuses.DONE,
        )
        s.add(glossary)
        s.flush()
        glossary_id = glossary.id

        gq = GlossaryQuery(s)
        gq.create_glossary_record(
            1,
            GlossaryRecordCreate(
                comment=None,
                source="Regional Effects",
                target="Региональные эффекты",
            ),
            glossary_id,
        )

        association = ProjectGlossaryAssociation(
            project_id=project_id, glossary_id=glossary_id
        )
        s.add(association)
        s.commit()

    response = user_logged_client.get(
        f"/projects/{project_id}/glossary_search?query=Nonexistent Term"
    )
    assert response.status_code == status.HTTP_200_OK
    response_json = response.json()
    assert response_json == []


def test_project_glossary_search_project_not_found(
    user_logged_client: TestClient,
):
    """Test searching glossaries for a non-existent project."""
    response = user_logged_client.get("/projects/999/glossary_search?query=test")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_get_project_translation_memories(
    user_logged_client: TestClient, session: Session
):
    """Test getting translation memories for a project."""
    with session as s:
        project = Project(created_by=1, name="Test Project")
        s.add(project)
        s.flush()
        project_id = project.id

        tm1 = TranslationMemory(name="test_tm1.tmx", created_by=1)
        tm2 = TranslationMemory(name="test_tm2.tmx", created_by=1)
        s.add_all([tm1, tm2])
        s.flush()
        tm1_id = tm1.id
        tm2_id = tm2.id

        association1 = ProjectTmAssociation(
            project_id=project_id, tm_id=tm1_id, mode="read"
        )
        association2 = ProjectTmAssociation(
            project_id=project_id, tm_id=tm2_id, mode="write"
        )
        s.add_all([association1, association2])
        s.commit()

    response = user_logged_client.get(f"/projects/{project_id}/translation_memories")
    assert response.status_code == status.HTTP_200_OK
    response_json = response.json()
    assert response_json["id"] == project_id
    assert len(response_json["translation_memories"]) == 2
    assert response_json["translation_memories"][0]["memory"]["id"] == tm1_id
    assert response_json["translation_memories"][0]["memory"]["name"] == "test_tm1.tmx"
    assert response_json["translation_memories"][0]["mode"] == "read"
    assert response_json["translation_memories"][1]["memory"]["id"] == tm2_id
    assert response_json["translation_memories"][1]["memory"]["name"] == "test_tm2.tmx"
    assert response_json["translation_memories"][1]["mode"] == "write"


def test_get_project_translation_memories_empty(
    user_logged_client: TestClient, session: Session
):
    """Test getting translation memories for a project with no TMs."""
    with session as s:
        project = Project(created_by=1, name="Test Project")
        s.add(project)
        s.commit()
        project_id = project.id

    response = user_logged_client.get(f"/projects/{project_id}/translation_memories")
    assert response.status_code == status.HTTP_200_OK
    response_json = response.json()
    assert response_json["id"] == project_id
    assert response_json["translation_memories"] == []


def test_get_project_translation_memories_not_found(user_logged_client: TestClient):
    """Test getting translation memories for a non-existent project."""
    response = user_logged_client.get("/projects/999/translation_memories")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_set_project_translation_memories(
    admin_logged_client: TestClient, session: Session
):
    """Test setting translation memories for a project."""
    with session as s:
        project = Project(created_by=1, name="Test Project")
        s.add(project)
        s.flush()
        project_id = project.id

        tm1 = TranslationMemory(name="test_tm1.tmx", created_by=1)
        tm2 = TranslationMemory(name="test_tm2.tmx", created_by=1)
        s.add_all([tm1, tm2])
        s.commit()
        tm1_id = tm1.id
        tm2_id = tm2.id

    response = admin_logged_client.post(
        f"/projects/{project_id}/translation_memories",
        json={
            "translation_memories": [
                {"id": tm1_id, "mode": "read"},
                {"id": tm2_id, "mode": "write"},
            ]
        },
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"message": "Translation memory list updated"}

    with session as s:
        associations = s.query(ProjectTmAssociation).all()
        assert len(associations) == 2
        assert associations[0].project_id == project_id
        assert associations[0].tm_id == tm1_id
        assert associations[0].mode.value == "read"
        assert associations[1].project_id == project_id
        assert associations[1].tm_id == tm2_id
        assert associations[1].mode.value == "write"


def test_set_project_translation_memories_multiple(
    admin_logged_client: TestClient, session: Session
):
    """Test setting multiple translation memories for a project."""
    with session as s:
        project = Project(created_by=1, name="Test Project")
        s.add(project)
        s.flush()
        project_id = project.id

        tm1 = TranslationMemory(name="test_tm1.tmx", created_by=1)
        tm2 = TranslationMemory(name="test_tm2.tmx", created_by=1)
        s.add_all([tm1, tm2])
        s.commit()
        tm1_id = tm1.id
        tm2_id = tm2.id

    response = admin_logged_client.post(
        f"/projects/{project_id}/translation_memories",
        json={
            "translation_memories": [
                {"id": tm1_id, "mode": "read"},
                {"id": tm2_id, "mode": "read"},
                {"id": tm1_id, "mode": "write"},
            ]
        },
    )
    assert response.status_code == status.HTTP_200_OK

    with session as s:
        associations = s.query(ProjectTmAssociation).all()
        assert len(associations) == 3


def test_set_project_translation_memories_replaces_existing(
    admin_logged_client: TestClient, session: Session
):
    """Test that setting translation memories replaces existing ones."""
    with session as s:
        project = Project(created_by=1, name="Test Project")
        s.add(project)
        s.flush()
        project_id = project.id

        tm1 = TranslationMemory(name="test_tm1.tmx", created_by=1)
        tm2 = TranslationMemory(name="test_tm2.tmx", created_by=1)
        s.add_all([tm1, tm2])
        s.flush()
        tm1_id = tm1.id
        tm2_id = tm2.id

        # Add initial association
        s.add(ProjectTmAssociation(project_id=project_id, tm_id=tm1_id, mode="read"))
        s.commit()

    # Replace with different TM
    response = admin_logged_client.post(
        f"/projects/{project_id}/translation_memories",
        json={"translation_memories": [{"id": tm2_id, "mode": "write"}]},
    )
    assert response.status_code == status.HTTP_200_OK

    with session as s:
        associations = s.query(ProjectTmAssociation).all()
        assert len(associations) == 1
        assert associations[0].tm_id == tm2_id
        assert associations[0].mode.value == "write"


def test_set_project_translation_memories_project_not_found(
    admin_logged_client: TestClient, session: Session
):
    """Test setting translation memories for a non-existent project."""
    with session as s:
        tm = TranslationMemory(name="test_tm.tmx", created_by=1)
        s.add(tm)
        s.commit()
        tm_id = tm.id

    response = admin_logged_client.post(
        "/projects/999/translation_memories",
        json={"translation_memories": [{"id": tm_id, "mode": "read"}]},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_set_project_translation_memories_tm_not_found(
    admin_logged_client: TestClient, session: Session
):
    """Test setting non-existent translation memories for a project."""
    with session as s:
        project = Project(created_by=1, name="Test Project")
        s.add(project)
        s.commit()
        project_id = project.id

    response = admin_logged_client.post(
        f"/projects/{project_id}/translation_memories",
        json={"translation_memories": [{"id": 999, "mode": "read"}]},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_set_project_translation_memories_multiple_writes(
    admin_logged_client: TestClient, session: Session
):
    """Test that setting multiple write mode TMs returns an error."""
    with session as s:
        project = Project(created_by=1, name="Test Project")
        s.add(project)
        s.flush()
        project_id = project.id

        tm1 = TranslationMemory(name="test_tm1.tmx", created_by=1)
        tm2 = TranslationMemory(name="test_tm2.tmx", created_by=1)
        s.add_all([tm1, tm2])
        s.commit()
        tm1_id = tm1.id
        tm2_id = tm2.id

    response = admin_logged_client.post(
        f"/projects/{project_id}/translation_memories",
        json={
            "translation_memories": [
                {"id": tm1_id, "mode": "write"},
                {"id": tm2_id, "mode": "write"},
            ]
        },
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert (
        "Only one translation memory can be set to write mode"
        in response.json()["detail"]
    )
