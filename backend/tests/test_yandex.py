import requests

from app.translators import yandex


def test_can_iterate_batches():
    lines = [f"line{i}" for i in range(2048)]

    last_idx = 0
    for batch in yandex.iterate_batches(lines):
        assert len(batch) > 0
        for line in batch:
            assert line == f"line{last_idx}"
            last_idx += 1

    assert last_idx == 2048


def test_batch_never_exceeds_10000_symbols():
    lines = [f"line{i}" for i in range(2048)]
    data = next(yandex.iterate_batches(lines))
    # measure the sum of all strings of the first batch
    total_len = 0
    for line in data:
        total_len += len(line)
    assert total_len <= 10000


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
