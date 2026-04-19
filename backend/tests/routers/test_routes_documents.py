import json
from datetime import datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.documents.models import (
    Document,
    DocumentRecord,
    DocumentRecordHistory,
    DocumentRecordHistoryChangeType,
    DocumentType,
    TxtDocument,
    TxtRecord,
    XliffDocument,
    XliffRecord,
)
from app.models import DocumentStatus
from app.projects.models import Project
from app.projects.query import ProjectQuery
from app.projects.schema import ProjectCreate
from app.schema import DocumentTask

# pylint: disable=C0116


def test_can_get_document(user_logged_client: TestClient, session: Session):
    with session as s:
        p = ProjectQuery(s).create_project(1, ProjectCreate(name="test"))
        records = [
            DocumentRecord(
                source="Regional Effects",
                target="Translation",
                word_count=2,
            ),
            DocumentRecord(
                source="User Interface",
                target="UI",
                word_count=2,
            ),
        ]
        s.add(
            Document(
                name="test_doc.txt",
                type=DocumentType.txt,
                records=records,
                processing_status="pending",
                created_by=1,
                project_id=p.id,
            )
        )
        s.commit()

    response = user_logged_client.get("/document/1")
    assert response.status_code == 200
    assert response.json() == {
        "id": 1,
        "name": "test_doc.txt",
        "status": "pending",
        "created_by": 1,
        "approved_records_count": 0,
        "total_records_count": 2,
        "type": "txt",
        "approved_word_count": 0,
        "total_word_count": 4,
        "project_id": 1,
    }


def test_returns_404_when_doc_not_found(user_logged_client: TestClient):
    response = user_logged_client.get("/document/1")
    assert response.status_code == 404


def test_can_delete_xliff_doc(admin_logged_client: TestClient, session: Session):
    with session as s:
        p = ProjectQuery(s).create_project(1, ProjectCreate(name="test"))
        s.add(
            XliffDocument(
                parent_id=1,
                original_document="",
            )
        )
        s.add(
            Document(
                name="first_doc.txt",
                type=DocumentType.txt,
                processing_status="waiting",
                created_by=1,
                project_id=p.id,
            )
        )
        s.commit()

    response = admin_logged_client.delete("/document/1")
    assert response.status_code == 200
    assert response.json() == {"message": "Deleted"}

    with session as s:
        assert s.query(Document).count() == 0
        assert s.query(XliffDocument).count() == 0


def test_can_delete_txt_doc(admin_logged_client: TestClient, session: Session):
    with session as s:
        p = ProjectQuery(s).create_project(1, ProjectCreate(name="test"))
        s.add(
            TxtDocument(
                parent_id=1,
                original_document="",
            )
        )
        s.add(
            Document(
                name="first_doc.txt",
                type=DocumentType.txt,
                processing_status="waiting",
                created_by=1,
                project_id=p.id,
            )
        )
        s.commit()

    response = admin_logged_client.delete("/document/1")
    assert response.status_code == 200
    assert response.json() == {"message": "Deleted"}

    with session as s:
        assert s.query(Document).count() == 0
        assert s.query(TxtDocument).count() == 0


def test_returns_404_when_deleting_nonexistent_doc(
    admin_logged_client: TestClient,
):
    response = admin_logged_client.delete("/document/1")
    assert response.status_code == 404


def test_upload_xliff(admin_logged_client: TestClient, session: Session):
    with session as s:
        ProjectQuery(s).create_project(1, ProjectCreate(name="test"))

    with open("tests/fixtures/small.xliff", "rb") as fp:
        response = admin_logged_client.post(
            "/document/", files={"file": fp}, data={"project_id": "1"}
        )
    assert response.status_code == 200

    with session as s:
        generic_doc = s.query(Document).filter_by(name="small.xliff").first()
        assert generic_doc is not None
        assert generic_doc.name == "small.xliff"
        assert generic_doc.type == DocumentType.xliff
        assert generic_doc.processing_status == "uploaded"
        assert generic_doc.user.id == 2
        assert not generic_doc.records

        xliff_doc = s.query(XliffDocument).filter_by(id=1).first()
        assert xliff_doc is not None
        assert xliff_doc.parent_id == generic_doc.id
        assert xliff_doc.original_document.startswith("<?xml version=")
        assert not xliff_doc.records


def test_upload_txt(admin_logged_client: TestClient, session: Session):
    with session as s:
        ProjectQuery(s).create_project(1, ProjectCreate(name="test"))

    with open("tests/fixtures/small.txt", "rb") as fp:
        response = admin_logged_client.post(
            "/document/", files={"file": fp}, data={"project_id": "1"}
        )
    assert response.status_code == 200

    with session as s:
        generic_doc = s.query(Document).filter_by(id=1).first()
        assert generic_doc is not None
        assert generic_doc.name == "small.txt"
        assert generic_doc.type == DocumentType.txt
        assert generic_doc.created_by == 2
        assert generic_doc.processing_status == "uploaded"
        assert not generic_doc.records

        txt_doc = s.query(TxtDocument).filter_by(id=1).first()
        assert txt_doc is not None
        assert txt_doc.parent_id == generic_doc.id
        assert txt_doc.original_document.startswith(
            "Soon after the characters enter Camp"
        )


def test_upload_no_file(admin_logged_client: TestClient):
    response = admin_logged_client.post("/document/", files={})
    assert response.status_code == 422


def test_upload_fails_with_unknown_type(
    admin_logged_client: TestClient, session: Session
):
    with session as s:
        ProjectQuery(s).create_project(1, ProjectCreate(name="test"))

    with open("tests/fixtures/small.tmx", "rb") as fp:
        response = admin_logged_client.post(
            "/document/", files={"file": fp}, data={"project_id": "1"}
        )
    assert response.status_code == 400


def test_upload_removes_old_files(admin_logged_client: TestClient, session: Session):
    with session as s:
        p = ProjectQuery(s).create_project(1, ProjectCreate(name="test"))
        s.add(
            Document(
                name="some_doc.txt",
                type=DocumentType.txt,
                processing_status=DocumentStatus.UPLOADED.value,
                upload_time=(datetime.now() - timedelta(days=2)),
                created_by=1,
                project_id=p.id,
            )
        )
        s.commit()

    with open("tests/fixtures/small.txt", "rb") as fp:
        response = admin_logged_client.post(
            "/document/", files={"file": fp}, data={"project_id": "1"}
        )
    assert response.status_code == 200

    with session as s:
        assert not s.query(Document).filter_by(name="some_doc.txt").first()


def test_upload_removes_only_uploaded_documents(
    admin_logged_client: TestClient, session: Session
):
    with session as s:
        p = ProjectQuery(s).create_project(1, ProjectCreate(name="test"))
        s.add(
            Document(
                name="uploaded_doc.txt",
                type=DocumentType.txt,
                processing_status=DocumentStatus.UPLOADED.value,
                upload_time=(datetime.now() - timedelta(days=2)),
                created_by=1,
                project_id=p.id,
            )
        )
        s.add(
            Document(
                name="processed_doc.xliff",
                type=DocumentType.xliff,
                processing_status=DocumentStatus.DONE.value,
                upload_time=(datetime.now() - timedelta(days=2)),
                created_by=1,
                project_id=p.id,
            )
        )
        s.commit()

    with open("tests/fixtures/small.txt", "rb") as fp:
        response = admin_logged_client.post(
            "/document/", files={"file": fp}, data={"project_id": "1"}
        )
    assert response.status_code == 200

    with session as s:
        assert not s.query(Document).filter_by(name="uploaded_doc.txt").first()
        assert s.query(Document).filter_by(name="processed_doc.xliff").first()


def test_process_sets_document_in_pending_stage_and_creates_task_xliff(
    admin_logged_client: TestClient, session: Session
):
    with session as s:
        ProjectQuery(s).create_project(1, ProjectCreate(name="test"))

    with open("tests/fixtures/small.xliff", "rb") as fp:
        admin_logged_client.post(
            "/document/", files={"file": fp}, data={"project_id": "1"}
        )

    response = admin_logged_client.post(
        "/document/1/process",
        json={
            "machine_translation_settings": None,
        },
    )

    assert response.status_code == 200

    with session as s:
        doc = s.query(Document).filter_by(id=1).one()
        assert doc.processing_status == "pending"


def test_process_sets_document_in_pending_stage_and_creates_task_txt(
    admin_logged_client: TestClient, session: Session
):
    with session as s:
        ProjectQuery(s).create_project(1, ProjectCreate(name="test"))

    with open("tests/fixtures/small.txt", "rb") as fp:
        admin_logged_client.post(
            "/document/", files={"file": fp}, data={"project_id": "1"}
        )

    response = admin_logged_client.post(
        "/document/1/process",
        json={
            "machine_translation_settings": None,
        },
    )

    assert response.status_code == 200

    with session as s:
        doc = s.query(Document).filter_by(id=1).one()
        assert doc.processing_status == "pending"


def test_process_creates_task_for_xliff(
    admin_logged_client: TestClient, session: Session
):
    with session as s:
        ProjectQuery(s).create_project(1, ProjectCreate(name="test"))

    with open("tests/fixtures/small.xliff", "rb") as fp:
        admin_logged_client.post(
            "/document/", files={"file": fp}, data={"project_id": "1"}
        )

    response = admin_logged_client.post(
        "/document/1/process",
        json={
            "machine_translation_settings": None,
        },
    )

    assert response.status_code == 200

    with session as s:
        tasks = s.query(DocumentTask).all()
        assert all([task.status == "pending" for task in tasks])
        assert len(tasks) == 3
        assert json.loads(tasks[0].data) == {
            "document_id": 1,
            "task_data": {
                "task_type": "create_segments",
            },
        }
        assert json.loads(tasks[1].data) == {
            "document_id": 1,
            "task_data": {
                "task_type": "substitute_segments",
                "settings": {
                    "similarity_threshold": 1.0,
                },
            },
        }
        assert json.loads(tasks[2].data) == {
            "document_id": 1,
            "task_data": {
                "task_type": "finalize_document",
            },
        }


def test_process_creates_task_for_txt(
    admin_logged_client: TestClient, session: Session
):
    with session as s:
        ProjectQuery(s).create_project(1, ProjectCreate(name="test"))

    with open("tests/fixtures/small.txt", "rb") as fp:
        admin_logged_client.post(
            "/document/", files={"file": fp}, data={"project_id": "1"}
        )

    response = admin_logged_client.post(
        "/document/1/process",
        json={
            "machine_translation_settings": None,
        },
    )

    assert response.status_code == 200

    with session as s:
        tasks = s.query(DocumentTask).all()
        assert all([task.status == "pending" for task in tasks])
        assert len(tasks) == 3
        assert json.loads(tasks[0].data) == {
            "document_id": 1,
            "task_data": {
                "task_type": "create_segments",
            },
        }
        assert json.loads(tasks[1].data) == {
            "document_id": 1,
            "task_data": {
                "task_type": "substitute_segments",
                "settings": {
                    "similarity_threshold": 1.0,
                },
            },
        }
        assert json.loads(tasks[2].data) == {
            "document_id": 1,
            "task_data": {
                "task_type": "finalize_document",
            },
        }


def test_returns_404_when_processing_nonexistent_doc(
    admin_logged_client: TestClient,
):
    response = admin_logged_client.post(
        "/document/1/process",
        json={
            "machine_translation_settings": None,
        },
    )
    assert response.status_code == 404


def test_download_xliff_doc(admin_logged_client: TestClient, session: Session):
    with session as s:
        ProjectQuery(s).create_project(1, ProjectCreate(name="test"))

    with open("tests/fixtures/small.xliff", "rb") as fp:
        admin_logged_client.post(
            "/document/", files={"file": fp}, data={"project_id": "1"}
        )

    with session as s:
        records = [
            DocumentRecord(document_id=1, source="Regional Effects", target="Some"),
            DocumentRecord(
                document_id=1,
                source="Other Effects",
                target="",
                approved=True,
            ),
            DocumentRecord(
                document_id=1,
                source="Regional Effects",
                target="Региональные эффекты",
                approved=True,
            ),
            DocumentRecord(document_id=1, source="123456789", target=""),
            XliffRecord(
                parent_id=1,
                segment_id=675606,
                document_id=1,
            ),
            XliffRecord(
                parent_id=2,
                segment_id=675607,
                document_id=1,
            ),
            XliffRecord(
                parent_id=3,
                segment_id=675608,
                document_id=1,
            ),
            XliffRecord(
                parent_id=4,
                segment_id=675609,
                document_id=1,
            ),
        ]
        s.add_all(records)
        s.commit()

    response = admin_logged_client.get("/document/1/download")
    assert response.status_code == 200

    data = response.read().decode("utf-8")
    assert data.startswith("<?xml version=")
    assert "Regional Effects" in data
    assert "Региональные эффекты" in data
    assert 'approved="yes"' in data
    assert "translated" in data
    assert "final" in data


def test_download_txt_doc(admin_logged_client: TestClient, session: Session):
    with session as s:
        ProjectQuery(s).create_project(1, ProjectCreate(name="test"))

    with open("tests/fixtures/small.txt", "rb") as fp:
        admin_logged_client.post(
            "/document/", files={"file": fp}, data={"project_id": "1"}
        )

    with session as s:
        txt_records = [
            DocumentRecord(
                document_id=1,
                source="Soon after the characters enter Camp Greenbriar, read or paraphrase the following text:",
                target="Вскоре после того, как персонажи войдут в Лагерь Гринбрайар, прочитайте или перефразируйте следующий текст:",
            ),
            DocumentRecord(
                document_id=1,
                source="“Hello, travelers!” calls an energetic giant sloth wearing a bracelet of claws and feathers.",
                target="«Здравствуйте, путешественники!» зовет энергичного гигантского ленивца с браслетом из когтей и перьев.",
            ),
            DocumentRecord(
                document_id=1,
                source="The creature dangles from a nearby tree and waves a three-clawed paw.",
                target="Существо свисает с ближайшего дерева и машет трехкогтевой лапой.",
            ),
            DocumentRecord(
                document_id=1,
                source="“Fresh faces are always welcome in Camp Greenbriar!”",
                target="«В лагере Гринбрайар всегда приветствуются свежие лица!»",
            ),
            DocumentRecord(
                document_id=1,
                source="The sloth is named Razak.",
                target="Ленивца зовут Разак.",
            ),
            DocumentRecord(
                document_id=1,
                source="He uses black bear stat block, with the following adjustments:",
                target="Он использует блок характеристик черного медведя со следующими изменениями:",
            ),
            TxtRecord(parent_id=1, document_id=1, offset=0),
            TxtRecord(parent_id=2, document_id=1, offset=89),
            TxtRecord(parent_id=3, document_id=1, offset=192),
            TxtRecord(parent_id=4, document_id=1, offset=252),
            TxtRecord(parent_id=5, document_id=1, offset=306),
            TxtRecord(parent_id=6, document_id=1, offset=332),
        ]
        s.add_all(txt_records)
        s.commit()

    response = admin_logged_client.get("/document/1/download")
    assert response.status_code == 200

    data = response.read().decode("utf-8")
    assert data.startswith("Вскоре после того, как персонажи")
    assert "Ленивца зовут Разак" in data
    assert "Он использует блок характеристик" in data


def test_download_shows_404_for_unknown_doc(admin_logged_client: TestClient):
    response = admin_logged_client.get("/document/1/download")
    assert response.status_code == 404


def test_get_doc_records_with_repetitions(
    user_logged_client: TestClient, session: Session
):
    """Test that document records endpoint returns repetition counts"""
    with session as s:
        p = ProjectQuery(s).create_project(1, ProjectCreate(name="test"))
        records = [
            DocumentRecord(source="Hello World", target="Привет Мир"),
            DocumentRecord(source="Goodbye", target="Пока"),
            DocumentRecord(source="Hello World", target="Здравствуйте Мир"),
            DocumentRecord(source="Test", target="Тест"),
            DocumentRecord(source="Hello World", target="Хелло Ворлд"),
        ]
        s.add(
            Document(
                name="test_doc.txt",
                type=DocumentType.txt,
                records=records,
                processing_status="pending",
                created_by=1,
                project_id=p.id,
            )
        )
        s.commit()

    response = user_logged_client.get("/document/1/records")
    assert response.status_code == 200
    response_json = response.json()

    # Should return all 5 records
    assert len(response_json["records"]) == 5

    # Check that repetition counts are correct
    # "Hello World" appears 3 times, others appear once
    record_counts = {
        record["source"]: record["repetitions_count"]
        for record in response_json["records"]
    }
    assert record_counts["Hello World"] == 3
    assert record_counts["Goodbye"] == 1
    assert record_counts["Test"] == 1


def test_update_document_name_only(admin_logged_client: TestClient, session: Session):
    """Test successful update of document name only."""
    p = ProjectQuery(session).create_project(1, ProjectCreate(name="test"))
    doc = Document(
        name="original.txt",
        type=DocumentType.txt,
        processing_status="done",
        created_by=1,
        project_id=p.id,
    )
    session.add(doc)
    session.commit()

    response = admin_logged_client.put(
        f"/document/{doc.id}", json={"name": "updated.txt"}
    )
    assert response.status_code == 200
    response_json = response.json()
    assert response_json["id"] == doc.id
    assert response_json["name"] == "updated.txt"
    assert response_json["project_id"] == 1

    with session as s:
        updated_doc = s.query(Document).filter_by(id=doc.id).first()
        assert updated_doc is not None
        assert updated_doc.name == "updated.txt"
        assert updated_doc.project_id == 1


def test_update_document_project_only(
    admin_logged_client: TestClient, session: Session
):
    """Test successful update of document project_id only."""
    p = ProjectQuery(session).create_project(1, ProjectCreate(name="test"))
    doc = Document(
        name="document.txt",
        type=DocumentType.txt,
        processing_status="done",
        created_by=1,
        project_id=p.id,
    )
    project = Project(created_by=1, name="Test Project")
    session.add(doc)
    session.add(project)
    session.commit()
    project_id = project.id  # Save id before session expires

    response = admin_logged_client.put(
        f"/document/{doc.id}", json={"project_id": project_id}
    )
    assert response.status_code == 200
    response_json = response.json()
    assert response_json["id"] == doc.id
    assert response_json["name"] == "document.txt"
    assert response_json["project_id"] == project_id

    with session as s:
        updated_doc = s.query(Document).filter_by(id=doc.id).first()
        assert updated_doc is not None
        assert updated_doc.project_id == project_id


def test_update_document_name_and_project(
    admin_logged_client: TestClient, session: Session
):
    """Test successful update of both name and project_id."""
    p = ProjectQuery(session).create_project(1, ProjectCreate(name="test"))
    doc = Document(
        name="original.txt",
        type=DocumentType.txt,
        processing_status="done",
        created_by=1,
        project_id=p.id,
    )
    project = Project(created_by=1, name="Test Project")
    session.add(doc)
    session.add(project)
    session.commit()
    project_id = project.id  # Save id before session expires

    response = admin_logged_client.put(
        f"/document/{doc.id}", json={"name": "updated.txt", "project_id": project_id}
    )
    assert response.status_code == 200
    response_json = response.json()
    assert response_json["id"] == doc.id
    assert response_json["name"] == "updated.txt"
    assert response_json["project_id"] == project_id

    with session as s:
        updated_doc = s.query(Document).filter_by(id=doc.id).first()
        assert updated_doc is not None
        assert updated_doc.name == "updated.txt"
        assert updated_doc.project_id == project_id


def test_update_document_not_found(admin_logged_client: TestClient):
    """Test 404 when document doesn't exist."""
    response = admin_logged_client.put("/document/999", json={"name": "updated.txt"})
    assert response.status_code == 404
    assert "Document not found" in response.json()["detail"]


def test_update_project_not_found(admin_logged_client: TestClient, session: Session):
    """Test 404 when project doesn't exist."""
    p = ProjectQuery(session).create_project(1, ProjectCreate(name="test"))
    doc = Document(
        name="document.txt",
        type=DocumentType.txt,
        processing_status="done",
        created_by=1,
        project_id=p.id,
    )
    session.add(doc)
    session.commit()

    response = admin_logged_client.put(f"/document/{doc.id}", json={"project_id": 999})
    assert response.status_code == 404
    assert "Project with id 999 not found" in response.json()["detail"]


def test_update_document_validation_error(
    admin_logged_client: TestClient, session: Session
):
    """Test 422 for invalid project_id (zero) or invalid name."""
    p = ProjectQuery(session).create_project(1, ProjectCreate(name="test"))
    doc = Document(
        name="document.txt",
        type=DocumentType.txt,
        processing_status="done",
        created_by=1,
        project_id=p.id,
    )
    session.add(doc)
    session.commit()

    # Test invalid project_id (negative)
    response = admin_logged_client.put(f"/document/{doc.id}", json={"project_id": -25})
    assert response.status_code == 404

    # Test invalid project_id (zero)
    response = admin_logged_client.put(f"/document/{doc.id}", json={"project_id": 0})
    assert response.status_code == 404

    # Test invalid name (empty)
    response = admin_logged_client.put(f"/document/{doc.id}", json={"name": ""})
    assert response.status_code == 422

    # Test invalid name (too long - over 255 characters)
    long_name = "a" * 256
    response = admin_logged_client.put(f"/document/{doc.id}", json={"name": long_name})
    assert response.status_code == 422


def test_update_document_unauthenticated(fastapi_client: TestClient, session: Session):
    """Test 401 when user is not authenticated."""
    p = ProjectQuery(session).create_project(1, ProjectCreate(name="test"))
    doc = Document(
        name="document.txt",
        type=DocumentType.txt,
        processing_status="done",
        created_by=1,
        project_id=p.id,
    )
    session.add(doc)
    session.commit()

    response = fastapi_client.put(f"/document/{doc.id}", json={"name": "updated.txt"})
    assert response.status_code == 401


def test_update_document_to_same_project(
    admin_logged_client: TestClient, session: Session
):
    """Test idempotent update to same project."""
    p = ProjectQuery(session).create_project(1, ProjectCreate(name="test"))
    doc = Document(
        name="document.txt",
        type=DocumentType.txt,
        processing_status="done",
        created_by=1,
        project_id=p.id,
    )
    project = Project(created_by=1, name="Test Project")
    session.add(doc)
    session.add(project)
    session.commit()
    project_id = project.id  # Save id before session expires

    response = admin_logged_client.put(
        f"/document/{doc.id}", json={"project_id": project_id}
    )
    assert response.status_code == 200
    response_json = response.json()
    assert response_json["id"] == doc.id
    assert response_json["name"] == "document.txt"
    assert response_json["project_id"] == project_id

    with session as s:
        updated_doc = s.query(Document).filter_by(id=doc.id).first()
        assert updated_doc is not None
        assert updated_doc.project_id == project_id


def test_download_original_xliff_doc(admin_logged_client: TestClient, session: Session):
    """Test downloading original XLIFF document."""
    with session as s:
        ProjectQuery(s).create_project(1, ProjectCreate(name="test"))

    with open("tests/fixtures/small.xliff", "rb") as fp:
        admin_logged_client.post(
            "/document/", files={"file": fp}, data={"project_id": "1"}
        )

    response = admin_logged_client.get("/document/1/download_original")
    assert response.status_code == 200

    data = response.read().decode("utf-8")
    assert data.startswith("<?xml version=")
    assert "Regional Effects" in data


def test_download_original_txt_doc(admin_logged_client: TestClient, session: Session):
    """Test downloading original TXT document."""
    with session as s:
        ProjectQuery(s).create_project(1, ProjectCreate(name="test"))

    with open("tests/fixtures/small.txt", "rb") as fp:
        admin_logged_client.post(
            "/document/", files={"file": fp}, data={"project_id": "1"}
        )

    response = admin_logged_client.get("/document/1/download_original")
    assert response.status_code == 200

    data = response.read().decode("utf-8")
    assert data.startswith("Soon after the characters enter Camp")
    assert "The sloth is named Razak" in data


def test_download_original_shows_404_for_unknown_doc(admin_logged_client: TestClient):
    """Test 404 when downloading original for non-existent document."""
    response = admin_logged_client.get("/document/1/download_original")
    assert response.status_code == 404


def test_download_xliff(admin_logged_client: TestClient, session: Session):
    """Test downloading document as XLIFF."""
    with session as s:
        p = ProjectQuery(s).create_project(1, ProjectCreate(name="test"))
        records = [
            DocumentRecord(
                source="Regional Effects",
                target="Региональные эффекты",
                approved=True,
            ),
            DocumentRecord(
                source="User Interface",
                target="Пользовательский интерфейс",
                approved=False,
            ),
        ]
        s.add(
            Document(
                name="test_doc.txt",
                type=DocumentType.txt,
                records=records,
                processing_status="pending",
                created_by=1,
                project_id=p.id,
            )
        )
        s.commit()

    response = admin_logged_client.get("/document/1/download_xliff")
    assert response.status_code == 200

    data = response.read().decode("utf-8")
    assert data.startswith("<?xml version=")
    assert "Regional Effects" in data
    assert "Региональные эффекты" in data
    assert "User Interface" in data
    assert "Пользовательский интерфейс" in data


def test_download_xliff_shows_404_for_unknown_doc(admin_logged_client: TestClient):
    """Test 404 when downloading XLIFF for non-existent document."""
    response = admin_logged_client.get("/document/1/download_xliff")
    assert response.status_code == 404


def test_upload_xliff_success(admin_logged_client: TestClient, session: Session):
    """Test successful XLIFF upload with record updates."""
    with session as s:
        p = ProjectQuery(s).create_project(1, ProjectCreate(name="test"))
        records = [
            DocumentRecord(
                source="Regional Effects",
                target="",
                approved=False,
            ),
            DocumentRecord(
                source="User Interface",
                target="",
                approved=False,
            ),
            DocumentRecord(
                source="Approved Segment",
                target="Old approved text",
                approved=True,
            ),
            DocumentRecord(
                source="123456789",
                target="",
                approved=False,
            ),
            DocumentRecord(
                source="Something else",
                target="",
                approved=False,
            ),
        ]
        s.add(
            Document(
                name="test_doc",
                type=DocumentType.txt,
                records=records,
                processing_status="done",
                created_by=1,
                project_id=p.id,
            )
        )
        s.commit()

    with open("tests/fixtures/upload_test.xliff", "rb") as fp:
        response = admin_logged_client.post(
            "/document/upload_xliff", files={"file": fp}, data={}
        )
    assert response.status_code == 200
    assert response.json() == {"message": "Successfully updated 3 record(s)"}

    with session as s:
        updated_records = s.query(DocumentRecord).filter_by(document_id=1).all()
        # Check that records with non-empty targets were updated
        regional_effects = next(
            (r for r in updated_records if r.source == "Regional Effects"), None
        )
        assert regional_effects
        assert regional_effects.target == "Региональные эффекты"
        assert regional_effects.approved is False

        user_interface = next(
            (r for r in updated_records if r.source == "User Interface"), None
        )
        assert user_interface
        assert user_interface.target == "Пользовательский интерфейс"
        assert user_interface.approved is False

        # Check that approved record was NOT updated
        approved_segment = next(
            (r for r in updated_records if r.source == "Approved Segment"), None
        )
        assert approved_segment
        assert approved_segment.target == "Old approved text"
        assert approved_segment.approved is True

        # Check that records with empty targets were NOT updated
        record_123456789 = next(
            (r for r in updated_records if r.source == "123456789"), None
        )
        assert record_123456789
        assert record_123456789.target == ""
        assert record_123456789.approved is False

        something_else = next(
            (r for r in updated_records if r.source == "Something else"), None
        )
        assert something_else
        assert something_else.target == "Что-то еще"
        assert something_else.approved is False


def test_upload_xliff_with_update_approved(
    admin_logged_client: TestClient, session: Session
):
    """Test XLIFF upload with update_approved=True to update approved records."""
    with session as s:
        p = ProjectQuery(s).create_project(1, ProjectCreate(name="test"))
        records = [
            DocumentRecord(
                source="Regional Effects",
                target="Old text",
                approved=True,
            ),
            DocumentRecord(
                source="User Interface",
                target="Old text",
                approved=False,
            ),
        ]
        s.add(
            Document(
                name="test_doc.xliff",
                type=DocumentType.xliff,
                records=records,
                processing_status="done",
                created_by=1,
                project_id=p.id,
            )
        )
        s.commit()

    with open("tests/fixtures/upload_test.xliff", "rb") as fp:
        response = admin_logged_client.post(
            "/document/upload_xliff",
            files={"file": fp},
            data={"update_approved": "true"},
        )
    assert response.status_code == 200
    assert response.json() == {"message": "Successfully updated 2 record(s)"}

    with session as s:
        updated_records = s.query(DocumentRecord).filter_by(document_id=1).all()
        # Check that approved record WAS updated
        regional_effects = next(
            (r for r in updated_records if r.source == "Regional Effects"), None
        )
        assert regional_effects
        assert regional_effects.target == "Региональные эффекты"
        assert regional_effects.approved is False  # it is False in XLIFF


def test_upload_xliff_document_not_found(admin_logged_client: TestClient):
    """Test XLIFF upload with non-existent document ID."""
    with open("tests/fixtures/upload_test.xliff", "rb") as fp:
        response = admin_logged_client.post(
            "/document/upload_xliff", files={"file": fp}, data={}
        )
    assert response.status_code == 404
    assert "Document not found" in response.json()["detail"]


def test_upload_xliff_invalid_format(admin_logged_client: TestClient):
    """Test XLIFF upload with invalid XLIFF format."""
    with open("tests/fixtures/small.txt", "rb") as fp:
        response = admin_logged_client.post(
            "/document/upload_xliff", files={"file": fp}
        )
    assert response.status_code == 400
    assert "Invalid XLIFF format" in response.json()["detail"]


def test_upload_xliff_history_tracking(
    admin_logged_client: TestClient, session: Session
):
    """Test that history entries are created for XLIFF upload."""
    with session as s:
        p = ProjectQuery(s).create_project(1, ProjectCreate(name="test"))
        records = [
            DocumentRecord(
                id=1,
                source="Regional Effects",
                target="Old text",
                approved=False,
            ),
            DocumentRecord(
                id=2,
                source="User Interface",
                target="Old text",
                approved=False,
            ),
        ]
        s.add(
            Document(
                name="test_doc",
                type=DocumentType.txt,
                records=records,
                processing_status="done",
                created_by=1,
                project_id=p.id,
            )
        )
        s.commit()

    with open("tests/fixtures/upload_test.xliff", "rb") as fp:
        response = admin_logged_client.post(
            "/document/upload_xliff", files={"file": fp}, data={}
        )
    assert response.status_code == 200

    with session as s:
        history_entries = (
            s.query(DocumentRecordHistory)
            .filter(DocumentRecordHistory.record_id.in_([1, 2]))
            .all()
        )
        assert len(history_entries) == 2
        assert all(
            h.change_type == DocumentRecordHistoryChangeType.translation_update
            for h in history_entries
        )
        assert all(h.author_id == 2 for h in history_entries)


def test_upload_xliff_unauthenticated(fastapi_client: TestClient):
    """Test that unauthenticated requests are rejected."""
    # Clear any existing cookies to ensure clean state
    fastapi_client.cookies.clear()

    with open("tests/fixtures/upload_test.xliff", "rb") as fp:
        response = fastapi_client.post("/document/upload_xliff", files={"file": fp})
    assert response.status_code == 401


def test_get_first_unapproved_returns_first_unapproved(
    user_logged_client: TestClient, session: Session
):
    """Test that the endpoint returns the first unapproved record."""
    with session as s:
        p = ProjectQuery(s).create_project(1, ProjectCreate(name="test"))
        records = [
            DocumentRecord(
                source="First",
                target="Первый",
                approved=True,
            ),
            DocumentRecord(
                source="Second",
                target="",
                approved=False,
            ),
            DocumentRecord(
                source="Third",
                target="",
                approved=False,
            ),
        ]
        s.add(
            Document(
                name="test_doc.txt",
                type=DocumentType.txt,
                records=records,
                processing_status="done",
                created_by=1,
                project_id=p.id,
            )
        )
        s.commit()

    response = user_logged_client.get("/document/1/first_unapproved")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 2
    assert data["source"] == "Second"
    assert data["approved"] is False


def test_get_first_unapproved_returns_null_when_all_approved(
    user_logged_client: TestClient, session: Session
):
    """Test that the endpoint returns null when all records are approved."""
    with session as s:
        p = ProjectQuery(s).create_project(1, ProjectCreate(name="test"))
        records = [
            DocumentRecord(source="First", target="Первый", approved=True),
            DocumentRecord(source="Second", target="Второй", approved=True),
        ]
        s.add(
            Document(
                name="test_doc.txt",
                type=DocumentType.txt,
                records=records,
                processing_status="done",
                created_by=1,
                project_id=p.id,
            )
        )
        s.commit()

    response = user_logged_client.get("/document/1/first_unapproved")
    assert response.status_code == 200
    assert response.json() is None


def test_get_first_unapproved_returns_null_when_no_records(
    user_logged_client: TestClient, session: Session
):
    """Test that the endpoint returns null when document has no records."""
    with session as s:
        p = ProjectQuery(s).create_project(1, ProjectCreate(name="test"))
        s.add(
            Document(
                name="test_doc.txt",
                type=DocumentType.txt,
                records=[],
                processing_status="done",
                created_by=1,
                project_id=p.id,
            )
        )
        s.commit()

    response = user_logged_client.get("/document/1/first_unapproved")
    assert response.status_code == 200
    assert response.json() is None


def test_get_first_unapproved_returns_404_for_unknown_doc(
    user_logged_client: TestClient,
):
    """Test that the endpoint returns 404 for non-existent document."""
    response = user_logged_client.get("/document/999/first_unapproved")
    assert response.status_code == 404
