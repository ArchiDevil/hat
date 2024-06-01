import requests

from app.translators import yandex


def test_can_iterate_batches():
    lines = [f"line{i}" for i in range(1024)]

    data = next(yandex.iterate_batches(lines, 256))
    assert len(data) == 256
    for i in range(256):
        assert f"line{i}" == data[i]


def test_batches_can_be_smaller():
    lines = [f"line{i}" for i in range(10)]

    data = next(yandex.iterate_batches(lines, 3))
    assert len(data) == 3
    for i in range(3):
        assert f"line{i}" == data[i]


def test_translator_gets_iam_token(monkeypatch):
    class FakeResponse:
        status_code = 200

        def json(self):
            return {"iamToken": "12345"}

    def fake_post(*args, **kwargs):
        assert args[0] == "https://iam.api.cloud.yandex.net/iam/v1/tokens"
        assert kwargs["json"] == {"yandexPassportOauthToken": "<PASSWORD>"}
        return FakeResponse()

    monkeypatch.setattr(requests, "post", fake_post)
    yandex.get_iam_token("<PASSWORD>")


def test_translator_translates_batch(monkeypatch):
    class FakeResponse:
        status_code = 200

        def json(self):
            return {"translations": [{"text": "line1"}, {"text": "line2"}]}

    def fake_post(*args, **kwargs):
        assert (
            args[0] == "https://translate.api.cloud.yandex.net/translate/v2/translate"
        )
        assert kwargs["json"] == {
            "folderId": "folder-id",
            "texts": ["line1", "line2"],
            "targetLanguageCode": "ru",
            "sourceLanguageCode": "en",
        }
        assert kwargs["headers"] == {
            "Content-Type": "application/json",
            "Authorization": "Bearer 12345",
        }
        return FakeResponse()

    monkeypatch.setattr(requests, "post", fake_post)
    yandex.translate_batch(["line1", "line2"], iam_token="12345", folder_id="folder-id")
