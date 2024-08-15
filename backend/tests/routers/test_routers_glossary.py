from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import GlossaryDocument
from app.glossary.query import GlossaryQuery
from main import app


def test_post_glossary_load_file(user_logged_client: TestClient, session: Session):
    """POST /glossary/load_file"""

    file = open("tests/fixtures/small_glossary.xlsx", "rb")
    path = app.url_path_for("create_glossary_doc_from_file")

    expected_json_resp = {"glossary_doc_id": 1}

    response = user_logged_client.post(
        url=path,
        files={"file": ("small_glossary.xlsx", file)},
        params={"document_name": "Document name"},
    )
    response_json = response.json()

    [document] = session.query(GlossaryDocument).all()
    [record_1, record_2] = document.records

    assert response.status_code == status.HTTP_201_CREATED
    assert expected_json_resp == response_json

    assert document.processing_status == "DONE"

    assert record_1.author == "Test User"
    assert record_2.author == "Test User"

    assert record_1.comment == "Названия книг"
    assert record_2.comment is None

    assert record_1.document_id == 1
    assert record_2.document_id == 1

    assert record_1.source == "Shadow of the Dragon Queen"
    assert record_2.source == "Age of Dreams"

    assert record_1.target == "Тень Королевы драконов"
    assert record_2.target == "Век Мечтаний"


def test_get_glossary_list_docs(user_logged_client: TestClient, session: Session):
    """GET /glossary/docs"""

    path = app.url_path_for("list_glossary_docs")

    doc_1 = GlossaryQuery(session).create_glossary_doc(
        user_id=1, document_name="Document name"
    )
    doc_2 = GlossaryQuery(session).create_glossary_doc(
        user_id=2, document_name="Document name"
    )

    response = user_logged_client.get(path)
    [resp_doc_1, resp_doc_2] = response.json()

    assert response.status_code == status.HTTP_200_OK

    assert resp_doc_1["processing_status"] == doc_1.processing_status
    assert resp_doc_1["user_id"] == doc_1.user_id

    assert resp_doc_2["processing_status"] == doc_2.processing_status
    assert resp_doc_2["user_id"] == doc_2.user_id


def test_get_glossary_retrieve_doc(user_logged_client: TestClient, session: Session):
    """GET /glossary/docs/{doc_id}"""

    doc_1 = GlossaryQuery(session).create_glossary_doc(
        user_id=1, document_name="Document name"
    )

    path = app.url_path_for("retrieve_glossary_doc", **{"glossary_doc_id": doc_1.id})

    response = user_logged_client.get(path)
    response_json = response.json()

    assert response.status_code == status.HTTP_200_OK

    assert response_json["id"] == doc_1.id
    assert response_json["processing_status"] == doc_1.processing_status
    assert response_json["user_id"] == doc_1.user_id


def test_update_glossary_doc(user_logged_client: TestClient, session: Session):
    """PUT /glossary/docs/{doc_id}"""

    expected_name = "New document name"

    doc_1 = GlossaryQuery(session).create_glossary_doc(
        user_id=1, document_name="Document name"
    )
    path = app.url_path_for("update_glossary_doc", **{"glossary_doc_id": doc_1.id})

    response = user_logged_client.put(url=path, json={"name": expected_name})
    response_json = response.json()

    assert response_json["name"] == expected_name


def test_list_glossary_records(user_logged_client: TestClient, session: Session):
    """GET /glossary/records"""

    doc = GlossaryQuery(session).create_glossary_doc(
        user_id=1, document_name="Document name"
    )
    rec = GlossaryQuery(session).create_glossary_record(
        author="Test",
        comment="Comment",
        source="Test",
        target="Тест",
        document_id=doc.id,
    )

    path = app.url_path_for("list_records_docs")

    response = user_logged_client.get(path)
    [resp_rec] = response.json()

    assert resp_rec["author"] == rec.author
    assert resp_rec["comment"] == rec.comment
    assert resp_rec["source"] == rec.source
    assert resp_rec["target"] == rec.target
    assert resp_rec["document_id"] == rec.document_id


def test_list_glossary_records_doc_filter(
    user_logged_client: TestClient, session: Session
):
    """GET /glossary/records?document_id={document_id}"""

    doc_1 = GlossaryQuery(session).create_glossary_doc(
        user_id=1, document_name="Document name"
    )
    doc_2 = GlossaryQuery(session).create_glossary_doc(
        user_id=1, document_name="Document name"
    )
    rec_1 = GlossaryQuery(session).create_glossary_record(
        author="Test",
        comment="Comment",
        source="Test",
        target="Тест",
        document_id=doc_1.id,
    )

    rec_2 = GlossaryQuery(session).create_glossary_record(
        author="Test 1",
        comment="Comment 1",
        source="Test 1",
        target="Тест 1",
        document_id=doc_2.id,
    )

    path = app.url_path_for("list_records_docs")

    response_doc_1, response_doc_2 = (
        user_logged_client.get(path, params={"document_id": doc_1.id}),
        user_logged_client.get(path, params={"document_id": doc_2.id}),
    )
    [resp_rec_1], [resp_rec_2] = (response_doc_1.json(), response_doc_2.json())

    assert resp_rec_1["author"] == rec_1.author
    assert resp_rec_1["comment"] == rec_1.comment
    assert resp_rec_1["source"] == rec_1.source
    assert resp_rec_1["target"] == rec_1.target
    assert resp_rec_1["document_id"] == rec_1.document_id

    assert resp_rec_2["author"] == rec_2.author
    assert resp_rec_2["comment"] == rec_2.comment
    assert resp_rec_2["source"] == rec_2.source
    assert resp_rec_2["target"] == rec_2.target
    assert resp_rec_2["document_id"] == rec_2.document_id
