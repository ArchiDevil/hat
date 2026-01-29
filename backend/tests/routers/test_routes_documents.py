import json
from datetime import datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.documents.models import (
    DocMemoryAssociation,
    Document,
    DocumentRecord,
    DocumentType,
    TmMode,
    TxtDocument,
    TxtRecord,
    XliffDocument,
    XliffRecord,
)
from app.documents.query import GenericDocsQuery
from app.glossary.models import ProcessingStatuses
from app.glossary.query import GlossaryQuery
from app.glossary.schema import (
    GlossaryRecordCreate,
    GlossarySchema,
)
from app.models import DocumentStatus
from app.projects.models import Project
from app.schema import DocumentTask
from app.translation_memory.models import TranslationMemory

# pylint: disable=C0116


def test_can_get_document(user_logged_client: TestClient, session: Session):
    with session as s:
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
        "project_id": None
    }


def test_returns_404_when_doc_not_found(user_logged_client: TestClient):
    response = user_logged_client.get("/document/1")
    assert response.status_code == 404


def test_can_delete_xliff_doc(user_logged_client: TestClient, session: Session):
    with session as s:
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
            )
        )
        s.commit()

    response = user_logged_client.delete("/document/1")
    assert response.status_code == 200
    assert response.json() == {"message": "Deleted"}

    with session as s:
        assert s.query(Document).count() == 0
        assert s.query(XliffDocument).count() == 0


def test_can_delete_txt_doc(user_logged_client: TestClient, session: Session):
    with session as s:
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
            )
        )
        s.commit()

    response = user_logged_client.delete("/document/1")
    assert response.status_code == 200
    assert response.json() == {"message": "Deleted"}

    with session as s:
        assert s.query(Document).count() == 0
        assert s.query(TxtDocument).count() == 0


def test_returns_404_when_deleting_nonexistent_doc(
    user_logged_client: TestClient,
):
    response = user_logged_client.delete("/document/1")
    assert response.status_code == 404


def test_upload_xliff(user_logged_client: TestClient, session: Session):
    with open("tests/fixtures/small.xliff", "rb") as fp:
        response = user_logged_client.post("/document/", files={"file": fp})
    assert response.status_code == 200

    with session as s:
        generic_doc = s.query(Document).filter_by(name="small.xliff").first()
        assert generic_doc is not None
        assert generic_doc.name == "small.xliff"
        assert generic_doc.type == DocumentType.xliff
        assert generic_doc.processing_status == "uploaded"
        assert generic_doc.user.id == 1
        assert not generic_doc.records

        xliff_doc = s.query(XliffDocument).filter_by(id=1).first()
        assert xliff_doc is not None
        assert xliff_doc.parent_id == generic_doc.id
        assert xliff_doc.original_document.startswith("<?xml version=")
        assert not xliff_doc.records


def test_upload_txt(user_logged_client: TestClient, session: Session):
    with open("tests/fixtures/small.txt", "rb") as fp:
        response = user_logged_client.post("/document/", files={"file": fp})
    assert response.status_code == 200

    with session as s:
        generic_doc = s.query(Document).filter_by(id=1).first()
        assert generic_doc is not None
        assert generic_doc.name == "small.txt"
        assert generic_doc.type == DocumentType.txt
        assert generic_doc.created_by == 1
        assert generic_doc.processing_status == "uploaded"
        assert not generic_doc.records

        txt_doc = s.query(TxtDocument).filter_by(id=1).first()
        assert txt_doc is not None
        assert txt_doc.parent_id == generic_doc.id
        assert txt_doc.original_document.startswith(
            "Soon after the characters enter Camp"
        )


def test_upload_no_file(user_logged_client: TestClient):
    response = user_logged_client.post("/document/", files={})
    assert response.status_code == 422


def test_upload_fails_with_unknown_type(user_logged_client: TestClient):
    with open("tests/fixtures/small.tmx", "rb") as fp:
        response = user_logged_client.post("/document/", files={"file": fp})
    assert response.status_code == 400


def test_upload_removes_old_files(user_logged_client: TestClient, session: Session):
    with session as s:
        s.add(
            Document(
                name="some_doc.txt",
                type=DocumentType.txt,
                processing_status=DocumentStatus.UPLOADED.value,
                upload_time=(datetime.now() - timedelta(days=2)),
                created_by=1,
            )
        )
        s.commit()

    with open("tests/fixtures/small.txt", "rb") as fp:
        response = user_logged_client.post("/document/", files={"file": fp})
    assert response.status_code == 200

    with session as s:
        assert not s.query(Document).filter_by(name="some_doc.txt").first()


def test_upload_removes_only_uploaded_documents(
    user_logged_client: TestClient, session: Session
):
    with session as s:
        s.add(
            Document(
                name="uploaded_doc.txt",
                type=DocumentType.txt,
                processing_status=DocumentStatus.UPLOADED.value,
                upload_time=(datetime.now() - timedelta(days=2)),
                created_by=1,
            )
        )
        s.add(
            Document(
                name="processed_doc.xliff",
                type=DocumentType.xliff,
                processing_status=DocumentStatus.DONE.value,
                upload_time=(datetime.now() - timedelta(days=2)),
                created_by=1,
            )
        )
        s.commit()

    with open("tests/fixtures/small.txt", "rb") as fp:
        response = user_logged_client.post("/document/", files={"file": fp})
    assert response.status_code == 200

    with session as s:
        assert not s.query(Document).filter_by(name="uploaded_doc.txt").first()
        assert s.query(Document).filter_by(name="processed_doc.xliff").first()


def test_process_sets_document_in_pending_stage_and_creates_task_xliff(
    user_logged_client: TestClient, session: Session
):
    with open("tests/fixtures/small.xliff", "rb") as fp:
        user_logged_client.post("/document/", files={"file": fp})

    response = user_logged_client.post(
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
    user_logged_client: TestClient, session: Session
):
    with open("tests/fixtures/small.txt", "rb") as fp:
        user_logged_client.post("/document/", files={"file": fp})

    response = user_logged_client.post(
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
    user_logged_client: TestClient, session: Session
):
    with open("tests/fixtures/small.xliff", "rb") as fp:
        user_logged_client.post("/document/", files={"file": fp})

    response = user_logged_client.post(
        "/document/1/process",
        json={
            "machine_translation_settings": None,
        },
    )

    assert response.status_code == 200

    with session as s:
        task = s.query(DocumentTask).filter_by(id=1).one()
        assert task.status == "pending"
        loaded_data = json.loads(task.data)
        assert loaded_data == {
            "type": "xliff",
            "document_id": 1,
            "settings": {
                "machine_translation_settings": None,
                "similarity_threshold": 1.0,
            },
        }


def test_process_creates_task_for_txt(user_logged_client: TestClient, session: Session):
    with open("tests/fixtures/small.txt", "rb") as fp:
        user_logged_client.post("/document/", files={"file": fp})

    response = user_logged_client.post(
        "/document/1/process",
        json={
            "machine_translation_settings": None,
        },
    )

    assert response.status_code == 200

    with session as s:
        task = s.query(DocumentTask).filter_by(id=1).one()
        assert task.status == "pending"
        loaded_data = json.loads(task.data)
        assert loaded_data == {
            "type": "txt",
            "document_id": 1,
            "settings": {
                "machine_translation_settings": None,
                "similarity_threshold": 1.0,
            },
        }


def test_returns_404_when_processing_nonexistent_doc(
    user_logged_client: TestClient,
):
    response = user_logged_client.post(
        "/document/1/process",
        json={
            "machine_translation_settings": None,
        },
    )
    assert response.status_code == 404


def test_download_xliff_doc(user_logged_client: TestClient, session: Session):
    with open("tests/fixtures/small.xliff", "rb") as fp:
        user_logged_client.post("/document/", files={"file": fp})

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
                state="needs-translation",
            ),
            XliffRecord(
                parent_id=2,
                segment_id=675607,
                document_id=1,
                state="needs-translation",
            ),
            XliffRecord(
                parent_id=3,
                segment_id=675608,
                document_id=1,
                state="translated",
            ),
            XliffRecord(
                parent_id=4,
                segment_id=675609,
                document_id=1,
                state="final",
            ),
        ]
        s.add_all(records)
        s.commit()

    response = user_logged_client.get("/document/1/download")
    assert response.status_code == 200

    data = response.read().decode("utf-8")
    assert data.startswith("<?xml version=")
    assert "Regional Effects" in data
    assert "Региональные эффекты" in data
    assert 'approved="yes"' in data
    assert "translated" in data
    assert "final" in data


def test_download_txt_doc(user_logged_client: TestClient, session: Session):
    with open("tests/fixtures/small.txt", "rb") as fp:
        user_logged_client.post("/document/", files={"file": fp})

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

    response = user_logged_client.get("/document/1/download")
    assert response.status_code == 200

    data = response.read().decode("utf-8")
    assert data.startswith("Вскоре после того, как персонажи")
    assert "Ленивца зовут Разак" in data
    assert "Он использует блок характеристик" in data


def test_download_shows_404_for_unknown_doc(user_logged_client: TestClient):
    response = user_logged_client.get("/document/1/download")
    assert response.status_code == 404


def test_returns_linked_tms(user_logged_client: TestClient, session: Session):
    with session as s:
        s.add(
            Document(
                name="small.xliff",
                type=DocumentType.xliff,
                created_by=1,
                processing_status="UPLOADED",
            )
        )
        s.add(TranslationMemory(name="first_doc.tmx", created_by=1))
        s.add(TranslationMemory(name="another_doc.tmx", created_by=1))
        s.add(DocMemoryAssociation(doc_id=1, tm_id=1, mode=TmMode.read))
        s.add(DocMemoryAssociation(doc_id=1, tm_id=2, mode=TmMode.read))
        s.commit()

    response = user_logged_client.get("/document/1/memories")
    assert response.status_code == 200
    assert response.json() == [
        {
            "document_id": 1,
            "memory": {"id": 1, "name": "first_doc.tmx", "created_by": 1},
            "mode": "read",
        },
        {
            "document_id": 1,
            "memory": {"id": 2, "name": "another_doc.tmx", "created_by": 1},
            "mode": "read",
        },
    ]


def test_sets_new_linked_tms(user_logged_client: TestClient, session: Session):
    with session as s:
        s.add(
            Document(
                name="small.xliff",
                type=DocumentType.xliff,
                created_by=1,
                processing_status="UPLOADED",
            )
        )
        s.add(TranslationMemory(name="first_doc.tmx", created_by=1))
        s.add(TranslationMemory(name="another_doc.tmx", created_by=1))
        s.commit()

    response = user_logged_client.post(
        "/document/1/memories",
        json={"memories": [{"id": 1, "mode": "read"}, {"id": 2, "mode": "write"}]},
    )
    assert response.status_code == 200

    with session as s:
        associations = s.query(DocMemoryAssociation).all()
        assert len(associations) == 2

        assert associations[0].doc_id == 1
        assert associations[0].tm_id == 1
        assert associations[0].mode == TmMode.read

        assert associations[1].doc_id == 1
        assert associations[1].tm_id == 2
        assert associations[1].mode == TmMode.write


def test_new_linked_tms_work_with_duplicated_ids(
    user_logged_client: TestClient, session: Session
):
    with session as s:
        s.add(
            Document(
                name="small.xliff",
                type=DocumentType.xliff,
                created_by=1,
                processing_status="UPLOADED",
            )
        )
        s.add(TranslationMemory(name="first_doc.tmx", created_by=1))
        s.add(TranslationMemory(name="another_doc.tmx", created_by=1))
        s.commit()

    response = user_logged_client.post(
        "/document/1/memories",
        json={
            "memories": [
                {"id": 1, "mode": "read"},
                {"id": 2, "mode": "read"},
                {"id": 2, "mode": "write"},
            ]
        },
    )
    assert response.status_code == 200

    with session as s:
        associations = s.query(DocMemoryAssociation).all()
        assert len(associations) == 3

        assert associations[0].doc_id == 1
        assert associations[0].tm_id == 1
        assert associations[0].mode == TmMode.read

        assert associations[1].doc_id == 1
        assert associations[1].tm_id == 2
        assert associations[1].mode == TmMode.read

        assert associations[2].doc_id == 1
        assert associations[2].tm_id == 2
        assert associations[2].mode == TmMode.write


def test_new_linked_tms_replaces_old_ones(
    user_logged_client: TestClient, session: Session
):
    with session as s:
        s.add(
            Document(
                name="small.xliff",
                type=DocumentType.xliff,
                created_by=1,
                processing_status="UPLOADED",
            )
        )
        s.add(TranslationMemory(name="first_doc.tmx", created_by=1))
        s.add(TranslationMemory(name="another_doc.tmx", created_by=1))
        s.add(DocMemoryAssociation(doc_id=1, tm_id=1, mode="read"))
        s.commit()

    response = user_logged_client.post(
        "/document/1/memories",
        json={"memories": [{"id": 2, "mode": "write"}]},
    )
    assert response.status_code == 200

    with session as s:
        associations = s.query(DocMemoryAssociation).all()
        assert len(associations) == 1

        assert associations[0].doc_id == 1
        assert associations[0].tm_id == 2
        assert associations[0].mode == TmMode.write


def test_set_linked_tms_fail_if_not_exists(
    user_logged_client: TestClient, session: Session
):
    with session as s:
        s.add(
            Document(
                name="small.xliff",
                type=DocumentType.xliff,
                created_by=1,
                processing_status="UPLOADED",
            )
        )
        s.commit()

    response = user_logged_client.post(
        "/document/1/memories",
        json={"memories": [{"id": 42, "mode": "read"}]},
    )
    assert response.status_code == 404


def test_set_linked_tms_fail_with_multiple_writes(
    user_logged_client: TestClient, session: Session
):
    with session as s:
        s.add_all(
            [
                Document(
                    name="small.xliff",
                    type=DocumentType.xliff,
                    created_by=1,
                    processing_status="UPLOADED",
                ),
                TranslationMemory(name="first_doc.tmx", created_by=1),
                TranslationMemory(name="another_doc.tmx", created_by=1),
            ]
        )
        s.commit()

    response = user_logged_client.post(
        "/document/1/memories",
        json={"memories": [{"id": 1, "mode": "write"}, {"id": 2, "mode": "write"}]},
    )
    assert response.status_code == 400


def test_can_get_glossaries_substitutions(
    user_logged_client: TestClient, session: Session
):
    dq = GenericDocsQuery(session)
    with session as s:
        records = [
            DocumentRecord(
                source="Regional Effects",
                target="",
            ),
            DocumentRecord(
                source="User Interface",
                target="",
            ),
        ]
        s.add(
            Document(
                name="test_doc.txt",
                type=DocumentType.txt,
                records=records,
                processing_status="pending",
                created_by=1,
            )
        )
        s.commit()

    gq = GlossaryQuery(session)
    g = gq.create_glossary(1, GlossarySchema(name="test"), ProcessingStatuses.DONE)
    gq.create_glossary_record(
        1,
        GlossaryRecordCreate(
            comment=None, source="Regional Effects", target="Региональные эффекты"
        ),
        g.id,
    )
    dq.set_document_glossaries(dq.get_document(1), [g])

    response = user_logged_client.get("/records/1/glossary_records")
    assert response.status_code == 200
    response_json = response.json()
    assert len(response_json) == 1
    assert response_json[0]["source"] == "Regional Effects"
    assert response_json[0]["target"] == "Региональные эффекты"
    assert response_json[0]["glossary_id"] == 1
    assert response_json[0]["comment"] is None
    assert response_json[0]["created_by_user"]["id"] == 1


def test_glossary_substitution_returns_404_for_non_existent_record(
    user_logged_client: TestClient, session: Session
):
    with session as s:
        records = [
            DocumentRecord(
                source="Regional Effects",
                target="",
            ),
            DocumentRecord(
                source="User Interface",
                target="",
            ),
        ]
        s.add(
            Document(
                name="test_doc.txt",
                type=DocumentType.txt,
                records=records,
                processing_status="pending",
                created_by=1,
            )
        )
        s.commit()

    response = user_logged_client.get("/records/999/glossary_records")
    assert response.status_code == 404


def test_can_get_linked_glossaries(user_logged_client: TestClient, session: Session):
    with session as s:
        records = [
            DocumentRecord(
                source="Regional Effects",
                target="",
            ),
            DocumentRecord(
                source="User Interface",
                target="",
            ),
        ]
        s.add(
            Document(
                name="test_doc.txt",
                type=DocumentType.txt,
                records=records,
                processing_status="pending",
                created_by=1,
            )
        )
        s.commit()

    gq = GlossaryQuery(session)
    g = gq.create_glossary(1, GlossarySchema(name="test"), ProcessingStatuses.DONE)
    gq.create_glossary_record(
        1,
        GlossaryRecordCreate(
            comment=None, source="Regional Effects", target="Региональные эффекты"
        ),
        g.id,
    )

    dq = GenericDocsQuery(session)
    dq.set_document_glossaries(dq.get_document(1), [g])

    response = user_logged_client.get("/document/1/glossaries")
    assert response.status_code == 200
    response_json = response.json()
    assert len(response_json) == 1
    assert response_json[0]["document_id"] == 1
    assert response_json[0]["glossary"]["name"] == "test"


def test_linked_glossaries_returns_404_for_non_existing_document(
    user_logged_client: TestClient,
):
    response = user_logged_client.get("/document/99/glossaries")
    assert response.status_code == 404


def test_can_set_glossaries_for_document(
    user_logged_client: TestClient, session: Session
):
    with session as s:
        s.add(
            Document(
                name="small.xliff",
                type=DocumentType.xliff,
                created_by=1,
                processing_status="UPLOADED",
            )
        )
        s.commit()

    gq = GlossaryQuery(session)
    g = gq.create_glossary(1, glossary=GlossarySchema(name="test_glossary"))
    glossary_id = g.id

    response = user_logged_client.post(
        "/document/1/glossaries",
        json={"glossaries": [{"id": glossary_id}]},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Glossary list updated"

    with session as s:
        doc = s.query(Document).filter_by(id=1).one()
        assert len(doc.glossaries) == 1
        assert doc.glossaries[0].id == glossary_id


def test_setting_glossaries_returns_404_for_non_existing_document(
    user_logged_client: TestClient,
):
    response = user_logged_client.post(
        "/document/99/glossaries",
        json={"glossaries": [{"id": 1}]},
    )
    assert response.status_code == 404


def test_setting_glossaries_returns_404_for_non_existing_glossaries(
    user_logged_client: TestClient, session: Session
):
    with session as s:
        s.add(
            Document(
                name="small.xliff",
                type=DocumentType.xliff,
                created_by=1,
                processing_status="UPLOADED",
            )
        )
        s.commit()

    gq = GlossaryQuery(session)
    gq.create_glossary(1, glossary=GlossarySchema(name="test_glossary"))

    response = user_logged_client.post(
        "/document/1/glossaries",
        json={"glossaries": [{"id": 99}]},
    )
    assert response.status_code == 404


def test_get_doc_records_with_repetitions(
    user_logged_client: TestClient, session: Session
):
    """Test that document records endpoint returns repetition counts"""
    with session as s:
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


def test_doc_glossary_search_with_matching_records(
    user_logged_client: TestClient, session: Session
):
    with session as s:
        records = [
            DocumentRecord(source="Regional Effects", target=""),
            DocumentRecord(source="User Interface", target=""),
        ]
        s.add(
            Document(
                name="test_doc.txt",
                type=DocumentType.txt,
                records=records,
                processing_status="pending",
                created_by=1,
            )
        )
        s.commit()

    gq = GlossaryQuery(session)
    g = gq.create_glossary(1, GlossarySchema(name="test"), ProcessingStatuses.DONE)
    gq.create_glossary_record(
        1,
        GlossaryRecordCreate(
            comment=None, source="Regional Effects", target="Региональные эффекты"
        ),
        g.id,
    )
    gq.create_glossary_record(
        1,
        GlossaryRecordCreate(
            comment=None, source="User Interface", target="Пользовательский интерфейс"
        ),
        g.id,
    )

    dq = GenericDocsQuery(session)
    dq.set_document_glossaries(dq.get_document(1), [g])

    response = user_logged_client.get(
        "/document/1/glossary_search?query=Regional Effects"
    )
    assert response.status_code == 200
    response_json = response.json()
    assert len(response_json) == 1
    assert response_json[0]["source"] == "Regional Effects"
    assert response_json[0]["target"] == "Региональные эффекты"
    assert response_json[0]["glossary_id"] == 1
    assert response_json[0]["comment"] is None
    assert response_json[0]["created_by_user"]["id"] == 1


def test_doc_glossary_search_returns_empty_when_no_glossaries(
    user_logged_client: TestClient, session: Session
):
    with session as s:
        records = [
            DocumentRecord(source="Regional Effects", target=""),
        ]
        s.add(
            Document(
                name="test_doc.txt",
                type=DocumentType.txt,
                records=records,
                processing_status="pending",
                created_by=1,
            )
        )
        s.commit()

    response = user_logged_client.get(
        "/document/1/glossary_search?query=Regional Effects"
    )
    assert response.status_code == 200
    assert response.json() == []


def test_doc_glossary_search_returns_empty_when_no_matches(
    user_logged_client: TestClient, session: Session
):
    with session as s:
        records = [
            DocumentRecord(source="Regional Effects", target=""),
        ]
        s.add(
            Document(
                name="test_doc.txt",
                type=DocumentType.txt,
                records=records,
                processing_status="pending",
                created_by=1,
            )
        )
        s.commit()

    gq = GlossaryQuery(session)
    g = gq.create_glossary(1, GlossarySchema(name="test"), ProcessingStatuses.DONE)
    gq.create_glossary_record(
        1,
        GlossaryRecordCreate(
            comment=None, source="Regional Effects", target="Региональные эффекты"
        ),
        g.id,
    )

    dq = GenericDocsQuery(session)
    dq.set_document_glossaries(dq.get_document(1), [g])

    response = user_logged_client.get(
        "/document/1/glossary_search?query=Nonexistent Term"
    )
    assert response.status_code == 200
    assert response.json() == []


def test_doc_glossary_search_returns_404_for_nonexistent_document(
    user_logged_client: TestClient,
):
    response = user_logged_client.get("/document/99/glossary_search?query=test")
    assert response.status_code == 404


def test_update_document_name_only(user_logged_client: TestClient, session: Session):
    """Test successful update of document name only."""
    doc = Document(
        name="original.txt",
        type=DocumentType.txt,
        processing_status="done",
        created_by=1,
    )
    session.add(doc)
    session.commit()

    response = user_logged_client.put(
        f"/document/{doc.id}", json={"name": "updated.txt"}
    )
    assert response.status_code == 200
    response_json = response.json()
    assert response_json["id"] == doc.id
    assert response_json["name"] == "updated.txt"
    assert response_json["project_id"] is None

    with session as s:
        updated_doc = s.query(Document).filter_by(id=doc.id).first()
        assert updated_doc is not None
        assert updated_doc.name == "updated.txt"
        assert updated_doc.project_id is None


def test_update_document_project_only(user_logged_client: TestClient, session: Session):
    """Test successful update of document project_id only."""
    doc = Document(
        name="document.txt",
        type=DocumentType.txt,
        processing_status="done",
        created_by=1,
    )
    project = Project(created_by=1, name="Test Project")
    session.add(doc)
    session.add(project)
    session.commit()
    project_id = project.id  # Save id before session expires

    response = user_logged_client.put(
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
    user_logged_client: TestClient, session: Session
):
    """Test successful update of both name and project_id."""
    doc = Document(
        name="original.txt",
        type=DocumentType.txt,
        processing_status="done",
        created_by=1,
    )
    project = Project(created_by=1, name="Test Project")
    session.add(doc)
    session.add(project)
    session.commit()
    project_id = project.id  # Save id before session expires

    response = user_logged_client.put(
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


def test_unassign_document_from_project(
    user_logged_client: TestClient, session: Session
):
    """Test successful unassignment of document from project."""
    doc = Document(
        name="document.txt",
        type=DocumentType.txt,
        processing_status="done",
        created_by=1,
        project_id=1,
    )
    project = Project(created_by=1, name="Test Project")
    session.add(doc)
    session.add(project)
    session.commit()

    response = user_logged_client.put(f"/document/{doc.id}", json={"project_id": None})
    assert response.status_code == 200
    response_json = response.json()
    assert response_json["id"] == doc.id
    assert response_json["name"] == "document.txt"
    assert response_json["project_id"] is None

    with session as s:
        updated_doc = s.query(Document).filter_by(id=doc.id).first()
        assert updated_doc is not None
        assert updated_doc.project_id is None


def test_update_document_not_found(user_logged_client: TestClient, session: Session):
    """Test 404 when document doesn't exist."""
    response = user_logged_client.put("/document/999", json={"name": "updated.txt"})
    assert response.status_code == 404
    assert "Document not found" in response.json()["detail"]


def test_update_project_not_found(user_logged_client: TestClient, session: Session):
    """Test 404 when project doesn't exist."""
    doc = Document(
        name="document.txt",
        type=DocumentType.txt,
        processing_status="done",
        created_by=1,
    )
    session.add(doc)
    session.commit()

    response = user_logged_client.put(f"/document/{doc.id}", json={"project_id": 999})
    assert response.status_code == 404
    assert "Project with id 999 not found" in response.json()["detail"]


def test_update_document_validation_error(
    user_logged_client: TestClient, session: Session
):
    """Test 422 for invalid project_id (negative, zero) or invalid name."""
    doc = Document(
        name="document.txt",
        type=DocumentType.txt,
        processing_status="done",
        created_by=1,
    )
    session.add(doc)
    session.commit()

    # Test invalid project_id (negative)
    response = user_logged_client.put(f"/document/{doc.id}", json={"project_id": -1})
    assert response.status_code == 422

    # Test invalid project_id (zero)
    response = user_logged_client.put(f"/document/{doc.id}", json={"project_id": 0})
    assert response.status_code == 422

    # Test invalid name (empty)
    response = user_logged_client.put(f"/document/{doc.id}", json={"name": ""})
    assert response.status_code == 422

    # Test invalid name (too long - over 255 characters)
    long_name = "a" * 256
    response = user_logged_client.put(f"/document/{doc.id}", json={"name": long_name})
    assert response.status_code == 422


def test_update_document_unauthenticated(fastapi_client: TestClient, session: Session):
    """Test 401 when user is not authenticated."""
    doc = Document(
        name="document.txt",
        type=DocumentType.txt,
        processing_status="done",
        created_by=1,
    )
    session.add(doc)
    session.commit()

    response = fastapi_client.put(f"/document/{doc.id}", json={"name": "updated.txt"})
    assert response.status_code == 401


def test_update_document_to_same_project(
    user_logged_client: TestClient, session: Session
):
    """Test idempotent update to same project."""
    doc = Document(
        name="document.txt",
        type=DocumentType.txt,
        processing_status="done",
        created_by=1,
        project_id=1,
    )
    project = Project(created_by=1, name="Test Project")
    session.add(doc)
    session.add(project)
    session.commit()
    project_id = project.id  # Save id before session expires

    response = user_logged_client.put(
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
