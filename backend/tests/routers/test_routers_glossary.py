import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import Glossary
from app.glossary.query import GlossaryQuery, NotFoundGlossaryRecordExc
from app.glossary.schema import (
    GlossaryRecordCreate,
    GlossaryRecordUpdate,
    GlossarySchema,
)
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

    assert record_1.created_by == 1
    assert record_2.created_by == 1

    assert record_1.comment == "Названия книг"
    assert record_2.comment is None

    assert record_1.glossary_id == 1
    assert record_2.glossary_id == 1

    assert record_1.source == "Shadow of the Dragon Queen"
    assert record_2.source == "Age of Dreams"

    assert record_1.stemmed_source == "shadow of the dragon queen"
    assert record_2.stemmed_source == "age of dream"

    assert record_1.target == "Тень Королевы драконов"
    assert record_2.target == "Век Мечтаний"


def test_get_glossary_list(user_logged_client: TestClient, session: Session):
    """GET /glossary/"""

    path = app.url_path_for("list_glossary")

    glossary_1 = GlossaryQuery(session).create_glossary(
        user_id=1, glossary=GlossarySchema(name="Glossary name")
    )
    glossary_2 = GlossaryQuery(session).create_glossary(
        user_id=2, glossary=GlossarySchema(name="Glossary name")
    )

    response = user_logged_client.get(path)
    [resp_1, resp_2] = response.json()

    assert response.status_code == status.HTTP_200_OK

    assert resp_1["processing_status"] == glossary_1.processing_status
    assert resp_1["created_by_user"]["id"] == glossary_1.created_by

    assert resp_2["processing_status"] == glossary_2.processing_status
    assert resp_2["created_by_user"]["id"] == glossary_2.created_by


def test_get_glossary_retrieve(user_logged_client: TestClient, session: Session):
    """GET /glossary/{glossary_id}/"""

    glossary_1 = GlossaryQuery(session).create_glossary(
        user_id=1, glossary=GlossarySchema(name="Glossary name")
    )

    path = app.url_path_for("retrieve_glossary", **{"glossary_id": glossary_1.id})

    response = user_logged_client.get(path)
    response_json = response.json()

    assert response.status_code == status.HTTP_200_OK

    assert response_json["id"] == glossary_1.id
    assert response_json["processing_status"] == glossary_1.processing_status
    assert response_json["created_by_user"]["id"] == glossary_1.created_by


def test_update_glossary(user_logged_client: TestClient, session: Session):
    """PUT /glossary/{glossary_id}/"""

    expected_name = "New glossary name"

    glossary_1 = GlossaryQuery(session).create_glossary(
        user_id=1, glossary=GlossarySchema(name="Glossary name")
    )
    path = app.url_path_for("update_glossary", **{"glossary_id": glossary_1.id})

    response = user_logged_client.put(url=path, json={"name": expected_name})
    response_json = response.json()

    assert response_json["name"] == expected_name


def test_list_glossary_records(user_logged_client: TestClient, session: Session):
    """GET /glossary/{glossary_id}/records/"""

    glossary = GlossaryQuery(session).create_glossary(
        user_id=1, glossary=GlossarySchema(name="Glossary name")
    )
    record_scheme = GlossaryRecordCreate(
        comment="Comment",
        source="Test",
        target="Тест",
    )
    record = GlossaryQuery(session).create_glossary_record(
        user_id=1,
        record=record_scheme,
        glossary_id=glossary.id,
    )

    path = app.url_path_for("list_records", **{"glossary_id": glossary.id})

    response = user_logged_client.get(path)
    [resp_rec] = response.json()

    assert resp_rec["created_by_user"]["id"] == record.created_by
    assert resp_rec["comment"] == record.comment
    assert resp_rec["source"] == record.source
    assert resp_rec["target"] == record.target
    assert resp_rec["glossary_id"] == record.glossary_id


def test_update_glossary_record(user_logged_client: TestClient, session: Session):
    """PUT /glossary/records/{record_id}/"""
    expected_user_id = 1
    repo = GlossaryQuery(session)
    glossary = repo.create_glossary(
        user_id=1, glossary=GlossarySchema(name="Glossary name")
    )
    record_scheme = GlossaryRecordCreate(
        comment="Comment",
        source="Test",
        target="Тест",
    )
    record = repo.create_glossary_record(
        user_id=1,
        record=record_scheme,
        glossary_id=glossary.id,
    )

    dumped_record = GlossaryRecordUpdate.model_validate(record)

    path = app.url_path_for("update_glossary_record", **{"record_id": record.id})
    response = user_logged_client.put(url=path, json=dumped_record.model_dump())
    response_json = response.json()

    assert response_json["created_by_user"]["id"] == expected_user_id

    record = repo.get_glossary_record_by_id(record.id)
    assert record.created_by == expected_user_id
    assert record.stemmed_source == "test"


def test_create_glossary(user_logged_client: TestClient, session: Session):
    """POST /glossary/"""
    expected_glossary_name = "Glossary name 1"
    path = app.url_path_for("create_glossary")
    dumped_glossary = GlossarySchema(name=expected_glossary_name)

    response = user_logged_client.post(url=path, json=dumped_glossary.model_dump())
    response_json = response.json()

    assert (
        GlossaryQuery(session).get_glossary(response_json["id"]).name
        == expected_glossary_name
    )


def test_delete_glossary(user_logged_client: TestClient, session: Session):
    """DELETE /glossary/{glossary_id}/"""
    glossary = GlossaryQuery(session).create_glossary(
        user_id=1, glossary=GlossarySchema(name="Glossary name")
    )
    path = app.url_path_for("delete_glossary", **{"glossary_id": glossary.id})

    response = user_logged_client.delete(url=path)
    response_json = response.json()

    assert response_json == {"message": "Deleted"}


def test_delete_glossary_with_records(user_logged_client: TestClient, session: Session):
    """DELETE /glossary/{glossary_id}/"""
    query = GlossaryQuery(session)
    glossary = query.create_glossary(
        user_id=1, glossary=GlossarySchema(name="Glossary name")
    )
    record_id = query.create_glossary_record(
        user_id=1,
        record=GlossaryRecordCreate(
            comment=None, source="some text", target="some target"
        ),
        glossary_id=glossary.id,
    ).id

    path = app.url_path_for("delete_glossary", **{"glossary_id": glossary.id})

    response = user_logged_client.delete(url=path)
    response_json = response.json()

    assert response_json == {"message": "Deleted"}
    # check that child was deleted
    with pytest.raises(NotFoundGlossaryRecordExc):
        query.get_glossary_record_by_id(record_id)


def test_delete_glossary_record(user_logged_client: TestClient, session: Session):
    """DELETE /glossary/records/{record_id}/"""
    repo = GlossaryQuery(session)
    glossary = repo.create_glossary(
        user_id=1, glossary=GlossarySchema(name="Glossary name")
    )
    record_scheme = GlossaryRecordCreate(
        comment="Comment",
        source="Test",
        target="Тест",
    )
    record = repo.create_glossary_record(
        user_id=1,
        record=record_scheme,
        glossary_id=glossary.id,
    )
    path = app.url_path_for("delete_glossary_record", **{"record_id": record.id})

    response = user_logged_client.delete(url=path)
    response_json = response.json()

    assert response_json == {"message": "Deleted"}


def test_create_glossary_record(user_logged_client: TestClient, session: Session):
    """POST /glossary/{glossary_id}/records"""
    repo = GlossaryQuery(session)
    glossary_id = repo.create_glossary(
        user_id=1, glossary=GlossarySchema(name="Glossary name")
    ).id
    record_scheme = GlossaryRecordCreate(
        comment="Comment",
        source="Test",
        target="Тест",
    )
    path = app.url_path_for("create_glossary_record", **{"glossary_id": glossary_id})
    response = user_logged_client.post(url=path, json=record_scheme.model_dump())
    response_json = response.json()

    assert response_json["created_by_user"]["id"] == 1
    assert response_json["comment"] == record_scheme.comment
    assert response_json["source"] == record_scheme.source
    assert response_json["target"] == record_scheme.target
    assert response_json["glossary_id"] == glossary_id

    assert repo.get_glossary_record_by_id(response_json["id"]).stemmed_source == "test"
