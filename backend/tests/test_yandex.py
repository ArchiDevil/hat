import time

import requests

from app.translators import yandex
from app.models import MachineTranslationSettings


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


def test_translator_handles_incorrect_status_code_with_iam_token(monkeypatch):
    class FakeResponse:
        status_code = 403
        text = "error message"

        def json(self):
            return None

    def fake_post(*args, **kwargs):
        assert args[0] == "https://iam.api.cloud.yandex.net/iam/v1/tokens"
        assert kwargs["json"] == {"yandexPassportOauthToken": "<PASSWORD>"}
        return FakeResponse()

    monkeypatch.setattr(requests, "post", fake_post)
    try:
        yandex.get_iam_token("<PASSWORD>")
        assert False
    except RuntimeError as e:
        assert "error message" in str(e)


def test_translator_handles_incorrect_answer_with_iam_token(monkeypatch):
    class FakeResponse:
        status_code = 200

        def json(self):
            return {}

    def fake_post(*args, **kwargs):
        assert args[0] == "https://iam.api.cloud.yandex.net/iam/v1/tokens"
        assert kwargs["json"] == {"yandexPassportOauthToken": "<PASSWORD>"}
        return FakeResponse()

    monkeypatch.setattr(requests, "post", fake_post)
    try:
        yandex.get_iam_token("<PASSWORD>")
        assert False
    except RuntimeError as e:
        assert "No IAM token returned" in str(e)


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


def test_translator_handles_errors(monkeypatch):
    class FakeResponse:
        status_code = 403
        text = "error message"

        def json(self):
            return None

    def fake_post(*_args, **_kwargs):
        return FakeResponse()

    monkeypatch.setattr(requests, "post", fake_post)
    try:
        yandex.translate_batch(
            ["line1", "line2"], iam_token="12345", folder_id="folder-id"
        )
        assert False
    except yandex.TranslationError as e:
        assert "error message" in str(e)


def test_translator_translates_everything(monkeypatch):
    class FakeIamResponse:
        status_code = 200

        def json(self):
            return {"iamToken": "12345"}

    class FakeTranslateResponse:
        status_code = 200

        def json(self):
            return {
                "translations": [
                    {
                        "text": "line1-translation",
                    },
                ]
            }

    def fake_post(*args, **kwargs):
        if args[0] == "https://iam.api.cloud.yandex.net/iam/v1/tokens":
            assert kwargs["json"] == {"yandexPassportOauthToken": "<PASSWORD>"}
            return FakeIamResponse()

        if args[0] == "https://translate.api.cloud.yandex.net/translate/v2/translate":
            assert kwargs["json"] == {
                "folderId": "folder-id",
                "texts": ["line1"],
                "sourceLanguageCode": "en",
                "targetLanguageCode": "ru",
            }
            return FakeTranslateResponse()

        assert False

    monkeypatch.setattr(requests, "post", fake_post)
    assert (["line1-translation"], False) == yandex.translate_lines(
        ["line1"],
        settings=MachineTranslationSettings(
            folder_id="folder-id", oauth_token="<PASSWORD>"
        ),
    )


def test_translator_returns_partial_when_fails(monkeypatch):
    class FakeIamResponse:
        status_code = 200

        def json(self):
            return {"iamToken": "12345"}

    class FakeTranslateResponse:
        def __init__(self, failed=False):
            self.__failed = failed

        @property
        def status_code(self):
            if self.__failed:
                return 403
            return 200

        @property
        def text(self):
            if self.__failed:
                return "error message"

            raise RuntimeError("should not be here")

        def json(self):
            if self.__failed:
                return None

            return {
                "translations": [
                    {
                        "text": "x" * 9900 + "-translation",
                    },
                ]
            }

    def fake_post(*args, **kwargs):
        if args[0] == "https://iam.api.cloud.yandex.net/iam/v1/tokens":
            assert kwargs["json"] == {"yandexPassportOauthToken": "<PASSWORD>"}
            return FakeIamResponse()

        if args[0] == "https://translate.api.cloud.yandex.net/translate/v2/translate":
            assert kwargs["json"]["folderId"] == "folder-id"
            assert kwargs["json"]["sourceLanguageCode"] == "en"
            assert kwargs["json"]["targetLanguageCode"] == "ru"

            # it always split to 2 parts
            assert len(kwargs["json"]["texts"]) == 1

            if kwargs["json"]["texts"][0].startswith("xxxx"):
                # first request
                return FakeTranslateResponse()

            if kwargs["json"]["texts"][0].startswith("yyyy"):
                return FakeTranslateResponse(failed=True)

        assert False

    monkeypatch.setattr(requests, "post", fake_post)

    # it fails and returns only a first part
    assert (["x" * 9900 + "-translation"], True) == yandex.translate_lines(
        ["x" * 9900, "y" * 9900],
        settings=MachineTranslationSettings(
            folder_id="folder-id", oauth_token="<PASSWORD>"
        ),
    )


def test_translator_requests_not_frequent(monkeypatch):
    class FakeIamResponse:
        status_code = 200

        def json(self):
            return {"iamToken": "12345"}

    class FakeTranslateResponse:
        @property
        def status_code(self):
            return 200

        def json(self):
            return {
                "translations": [
                    {
                        "text": "x" * 9900 + "-translation",
                    },
                ]
            }

    def fake_post(*args, **kwargs):
        if args[0] == "https://iam.api.cloud.yandex.net/iam/v1/tokens":
            assert kwargs["json"] == {"yandexPassportOauthToken": "<PASSWORD>"}
            return FakeIamResponse()

        if args[0] == "https://translate.api.cloud.yandex.net/translate/v2/translate":
            assert kwargs["json"]["folderId"] == "folder-id"
            assert kwargs["json"]["sourceLanguageCode"] == "en"
            assert kwargs["json"]["targetLanguageCode"] == "ru"
            assert len(kwargs["json"]["texts"]) == 1
            return FakeTranslateResponse()

        assert False

    monkeypatch.setattr(requests, "post", fake_post)

    now = time.time()
    yandex.translate_lines(
        ["x" * 9900 for _ in range(21)],
        settings=MachineTranslationSettings(
            folder_id="folder-id", oauth_token="<PASSWORD>"
        ),
    )

    # check that 21 request takes more than a second
    assert time.time() - now > 1.0
