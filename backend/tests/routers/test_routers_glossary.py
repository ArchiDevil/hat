from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import Glossary
from app.glossary.query import GlossaryQuery
from main import app


def test_post_glossary_load_file(user_logged_client: TestClient, session: Session):
    """POST /glossary/load_file/"""

    file = open("tests/fixtures/small_glossary.xlsx", "rb")
    path = app.url_path_for("create_glossary_from_file")

    expected_json_resp = {"glossary_id": 1}

    response = user_logged_client.post(
        url=path,
        files={"file": ("small_glossary.xlsx", file)},
        params={"glossary_name": "Glossary name"},
    )
    response_json = response.json()

    [glossary] = session.query(Glossary).all()
    [record_1, record_2] = glossary.records

    assert response.status_code == status.HTTP_201_CREATED
    assert expected_json_resp == response_json

    assert glossary.processing_status == "DONE"

    assert record_1.author == "Test User"
    assert record_2.author == "Test User"

    assert record_1.comment == "Названия книг"
    assert record_2.comment is None

    assert record_1.glossary_id == 1
    assert record_2.glossary_id == 1

    assert record_1.source == "Shadow of the Dragon Queen"
    assert record_2.source == "Age of Dreams"

    assert record_1.target == "Тень Королевы драконов"
    assert record_2.target == "Век Мечтаний"


def test_get_glossary_list(user_logged_client: TestClient, session: Session):
    """GET /glossary/"""

    path = app.url_path_for("list_glossary")

    glossary_1 = GlossaryQuery(session).create_glossary(
        user_id=1, glossary_name="Glossary name"
    )
    glossary_2 = GlossaryQuery(session).create_glossary(
        user_id=2, glossary_name="Glossary name"
    )

    response = user_logged_client.get(path)
    [resp_1, resp_2] = response.json()

    assert response.status_code == status.HTTP_200_OK

    assert resp_1["processing_status"] == glossary_1.processing_status
    assert resp_1["user_id"] == glossary_1.user_id

    assert resp_2["processing_status"] == glossary_2.processing_status
    assert resp_2["user_id"] == glossary_2.user_id


def test_get_glossary_retrieve(user_logged_client: TestClient, session: Session):
    """GET /glossary/{glossary_id}/"""

    glossary_1 = GlossaryQuery(session).create_glossary(
        user_id=1, glossary_name="Glossary name"
    )

    path = app.url_path_for("retrieve_glossary", **{"glossary_id": glossary_1.id})

    response = user_logged_client.get(path)
    response_json = response.json()

    assert response.status_code == status.HTTP_200_OK

    assert response_json["id"] == glossary_1.id
    assert response_json["processing_status"] == glossary_1.processing_status
    assert response_json["user_id"] == glossary_1.user_id


def test_update_glossary(user_logged_client: TestClient, session: Session):
    """PUT /glossary/{glossary_id}/"""

    expected_name = "New glossary name"

    glossary_1 = GlossaryQuery(session).create_glossary(
        user_id=1, glossary_name="Glossary name"
    )
    path = app.url_path_for("update_glossary", **{"glossary_id": glossary_1.id})

    response = user_logged_client.put(url=path, json={"name": expected_name})
    response_json = response.json()

    assert response_json["name"] == expected_name


def test_list_glossary_records(user_logged_client: TestClient, session: Session):
    """GET /glossary/{glossary_id}/records/"""

    glossary = GlossaryQuery(session).create_glossary(
        user_id=1, glossary_name="Glossary name"
    )
    rec = GlossaryQuery(session).create_glossary_record(
        author="Test",
        comment="Comment",
        source="Test",
        target="Тест",
        glossary_id=glossary.id,
    )

    path = app.url_path_for("list_records", **{"glossary_id": glossary.id})

    response = user_logged_client.get(path)
    [resp_rec] = response.json()

    assert resp_rec["author"] == rec.author
    assert resp_rec["comment"] == rec.comment
    assert resp_rec["source"] == rec.source
    assert resp_rec["target"] == rec.target
    assert resp_rec["glossary_id"] == rec.glossary_id
