from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import GlossaryDocument
from app.glossary.query import GlossaryDocsQuery
from main import app


def test_post_glossary_load_file(user_logged_client: TestClient, session: Session):
    """POST /glossary/load_file"""

    file = open("tests/fixtures/small_glossary.xlsx", "rb")
    path = app.url_path_for("create_glossary_doc_from_file")

    expected_json_resp = {"glossary_doc_id": 1}

    response = user_logged_client.post(
        url=path,
        files={"uploaded_file": ("small_glossary.xlsx", file)},
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

    doc_1 = GlossaryDocsQuery(session).create_glossary_doc(user_id=1)
    doc_2 = GlossaryDocsQuery(session).create_glossary_doc(user_id=2)

    response = user_logged_client.get(path)
    [resp_doc_1, resp_doc_2] = response.json()

    assert response.status_code == status.HTTP_200_OK

    assert resp_doc_1["processing_status"] == doc_1.processing_status
    assert resp_doc_1["user_id"] == doc_1.user_id

    assert resp_doc_2["processing_status"] == doc_2.processing_status
    assert resp_doc_2["user_id"] == doc_2.user_id


def test_get_glossary_retrieve_doc(user_logged_client: TestClient, session: Session):
    """GET /glossary/docs/{doc_id}"""

    doc_1 = GlossaryDocsQuery(session).create_glossary_doc(user_id=1)

    path = app.url_path_for("retrieve_glossary_doc", **{"glossary_doc_id": doc_1.id})

    response = user_logged_client.get(path)
    response_json = response.json()

    assert response.status_code == status.HTTP_200_OK

    assert response_json["id"] == doc_1.id
    assert response_json["processing_status"] == doc_1.processing_status
    assert response_json["user_id"] == doc_1.user_id
