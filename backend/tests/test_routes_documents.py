import json
from datetime import datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import models, schema
from app.documents.models import (
    Document,
    DocumentRecord,
    DocumentType,
    TxtDocument,
    TxtRecord,
    XliffDocument,
    XliffRecord,
)

# pylint: disable=C0116


def test_can_get_list_of_docs(user_logged_client: TestClient, session: Session):
    with session as s:
        s.add_all(
            [
                Document(
                    name="first_doc.txt",
                    type=DocumentType.TXT,
                    processing_status="pending",
                    created_by=1,
                ),
                Document(
                    name="another_doc.xliff",
                    type=DocumentType.XLIFF,
                    processing_status="done",
                    created_by=1,
                ),
            ]
        )
        s.commit()

    response = user_logged_client.get("/document")
    assert response.status_code == 200
    assert response.json() == [
        {"id": 1, "name": "first_doc.txt", "status": "pending", "created_by": 1},
        {"id": 2, "name": "another_doc.xliff", "status": "done", "created_by": 1},
    ]


def test_can_get_document(user_logged_client: TestClient, session: Session):
    with session as s:
        records = [
            DocumentRecord(
                source="Regional Effects",
                target="Translation",
            ),
            DocumentRecord(
                source="User Interface",
                target="UI",
            ),
        ]
        s.add(
            Document(
                name="test_doc.txt",
                type=DocumentType.TXT,
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
        "records_count": 2,
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
                type=DocumentType.TXT,
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
                type=DocumentType.TXT,
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


# TODO: check that TXT and XLIFF are possible to upload
def test_upload_xliff(user_logged_client: TestClient, session: Session):
    with open("tests/fixtures/small.xliff", "rb") as fp:
        response = user_logged_client.post("/document/", files={"file": fp})
    assert response.status_code == 200

    with session as s:
        generic_doc = s.query(Document).filter_by(name="small.xliff").first()
        assert generic_doc is not None
        assert generic_doc.name == "small.xliff"
        assert generic_doc.type == DocumentType.XLIFF
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
        assert generic_doc.type == DocumentType.TXT
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
                type=DocumentType.TXT,
                processing_status=models.DocumentStatus.UPLOADED.value,
                upload_time=(datetime.now() - timedelta(days=2)),
                created_by=1,
            )
        )
        s.commit()

    with open("tests/fixtures/small.txt", "rb") as fp:
        response = user_logged_client.post("/document/", files={"file": fp})
    assert response.status_code == 200

    with session as s:
        doc = s.query(Document).filter_by(name="some_doc.txt").first()
        assert not doc


def test_upload_removes_only_uploaded_documents(
    user_logged_client: TestClient, session: Session
):
    with session as s:
        s.add(
            Document(
                name="uploaded_doc.txt",
                type=DocumentType.TXT,
                processing_status=models.DocumentStatus.UPLOADED.value,
                upload_time=(datetime.now() - timedelta(days=2)),
                created_by=1,
            )
        )
        s.add(
            Document(
                name="processed_doc.xliff",
                type=DocumentType.XLIFF,
                processing_status=models.DocumentStatus.DONE.value,
                upload_time=(datetime.now() - timedelta(days=2)),
                created_by=1,
            )
        )
        s.commit()

    with open("tests/fixtures/small.txt", "rb") as fp:
        response = user_logged_client.post("/document/", files={"file": fp})
    assert response.status_code == 200

    with session as s:
        doc = s.query(Document).filter_by(name="uploaded_doc.txt").first()
        assert not doc
        doc = s.query(Document).filter_by(name="processed_doc.xliff").first()
        assert doc


def test_process_sets_document_in_pending_stage_and_creates_task_xliff(
    user_logged_client: TestClient, session: Session
):
    with open("tests/fixtures/small.xliff", "rb") as fp:
        user_logged_client.post("/document/", files={"file": fp})

    response = user_logged_client.post(
        "/document/1/process",
        json={
            "substitute_numbers": False,
            "machine_translation_settings": None,
            "tmx_file_ids": [],
            "tmx_usage": "newest",
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
            "substitute_numbers": False,
            "machine_translation_settings": None,
            "tmx_file_ids": [],
            "tmx_usage": "newest",
        },
    )

    assert response.status_code == 200

    with session as s:
        doc = s.query(Document).filter_by(id=1).one()
        assert doc.processing_status == "pending"


def test_process_creates_task_for_xliff(
    user_logged_client: TestClient, session: Session
):
    with session as s:
        s.add(schema.TmxDocument(name="first_doc.tmx", created_by=1))

    with open("tests/fixtures/small.xliff", "rb") as fp:
        user_logged_client.post("/document/", files={"file": fp})

    response = user_logged_client.post(
        "/document/1/process",
        json={
            "substitute_numbers": False,
            "machine_translation_settings": None,
            "tmx_file_ids": [1],
            "tmx_usage": "newest",
        },
    )

    assert response.status_code == 200

    with session as s:
        task = s.query(schema.DocumentTask).filter_by(id=1).one()
        assert task.status == "pending"
        loaded_data = json.loads(task.data)
        assert loaded_data == {
            "type": "xliff",
            "document_id": 1,
            "settings": {
                "substitute_numbers": False,
                "machine_translation_settings": None,
                "tmx_file_ids": [1],
                "tmx_usage": "newest",
                "similarity_threshold": 1.0,
            },
        }


def test_process_creates_task_for_txt(user_logged_client: TestClient, session: Session):
    with session as s:
        s.add(schema.TmxDocument(name="first_doc.tmx", created_by=1))

    with open("tests/fixtures/small.txt", "rb") as fp:
        user_logged_client.post("/document/", files={"file": fp})

    response = user_logged_client.post(
        "/document/1/process",
        json={
            "substitute_numbers": False,
            "machine_translation_settings": None,
            "tmx_file_ids": [1],
            "tmx_usage": "newest",
        },
    )

    assert response.status_code == 200

    with session as s:
        task = s.query(schema.DocumentTask).filter_by(id=1).one()
        assert task.status == "pending"
        loaded_data = json.loads(task.data)
        assert loaded_data == {
            "type": "txt",
            "document_id": 1,
            "settings": {
                "substitute_numbers": False,
                "machine_translation_settings": None,
                "tmx_file_ids": [1],
                "tmx_usage": "newest",
                "similarity_threshold": 1.0,
            },
        }


def test_process_creates_xliff_doc_tmx_link(
    user_logged_client: TestClient, session: Session
):
    with session as s:
        s.add(schema.TmxDocument(name="first_doc.tmx", created_by=1))
        s.add(schema.TmxDocument(name="another_doc.tmx", created_by=1))
        s.commit()

    with open("tests/fixtures/small.xliff", "rb") as fp:
        user_logged_client.post("/document/", files={"file": fp})

    response = user_logged_client.post(
        "/document/1/process",
        json={
            "substitute_numbers": False,
            "machine_translation_settings": None,
            "tmx_file_ids": [1, 2],
            "tmx_usage": "newest",
        },
    )

    assert response.status_code == 200

    with session as s:
        doc = s.query(Document).filter_by(id=1).one()
        assert len(doc.tmxs) == 2
        assert doc.tmxs[0].id == 1
        assert doc.tmxs[1].id == 2


def test_process_creates_txt_doc_tmx_link(
    user_logged_client: TestClient, session: Session
):
    with session as s:
        s.add(schema.TmxDocument(name="first_doc.tmx", created_by=1))
        s.add(schema.TmxDocument(name="another_doc.tmx", created_by=1))
        s.commit()

    with open("tests/fixtures/small.txt", "rb") as fp:
        user_logged_client.post("/document/", files={"file": fp})

    response = user_logged_client.post(
        "/document/1/process",
        json={
            "substitute_numbers": False,
            "machine_translation_settings": None,
            "tmx_file_ids": [1, 2],
            "tmx_usage": "newest",
        },
    )

    assert response.status_code == 200

    with session as s:
        doc = s.query(Document).filter_by(id=1).one()
        assert len(doc.tmxs) == 2
        assert doc.tmxs[0].id == 1
        assert doc.tmxs[1].id == 2


def test_returns_404_when_processing_nonexistent_doc(
    user_logged_client: TestClient,
):
    response = user_logged_client.post(
        "/document/1/process",
        json={
            "substitute_numbers": False,
            "machine_translation_settings": None,
            "tmx_file_ids": [],
            "tmx_usage": "newest",
        },
    )
    assert response.status_code == 404


def test_download_xliff_doc(user_logged_client: TestClient, session: Session):
    with open("tests/fixtures/small.xliff", "rb") as fp:
        user_logged_client.post("/document/", files={"file": fp})

    with session as s:
        records = [
            DocumentRecord(document_id=1, source="Regional Effects", target="Some"),
            DocumentRecord(document_id=1, source="Other Effects", target=""),
            DocumentRecord(
                document_id=1,
                source="Regional Effects",
                target="Региональные эффекты",
            ),
            DocumentRecord(document_id=1, source="123456789", target=""),
            XliffRecord(
                parent_id=1,
                segment_id=675606,
                document_id=1,
                state="needs-translation",
                approved=False,
            ),
            XliffRecord(
                parent_id=2,
                segment_id=675607,
                document_id=1,
                state="needs-translation",
                approved=True,
            ),
            XliffRecord(
                parent_id=3,
                segment_id=675608,
                document_id=1,
                state="translated",
                approved=True,
            ),
            XliffRecord(
                parent_id=4,
                segment_id=675609,
                document_id=1,
                state="final",
                approved=False,
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
            TxtRecord(
                parent_id=1,
                document_id=1,
                offset=0,
            ),
            TxtRecord(
                parent_id=2,
                document_id=1,
                offset=89,
            ),
            TxtRecord(
                parent_id=3,
                document_id=1,
                offset=192,
            ),
            TxtRecord(
                parent_id=4,
                document_id=1,
                offset=252,
            ),
            TxtRecord(
                parent_id=5,
                document_id=1,
                offset=306,
            ),
            TxtRecord(
                parent_id=6,
                document_id=1,
                offset=332,
            ),
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
