import json
import logging
import time
from typing import Generator

import requests
from pydantic import BaseModel, PositiveInt, ValidationError

from app.models import MachineTranslationSettings
from app.settings import get_settings


class YandexTranslatorResponse(BaseModel):
    """
    A response object from Yandex Translator API.

    Attributes:
        translations (list[dict]): A list of translation results.
    """

    translations: list[dict[str, str]]


class TranslationError(Exception):
    """
    An error raised when Yandex Translator API returns an error.
    """


# Currently Yandex rejects requests larger than 10k symbols.
def iterate_batches(
    lines: list[str], max_batch_size: PositiveInt = 10000
) -> Generator[list[str], None, None]:
    output = []
    last_len = 0
    i = 0
    while i < len(lines):
        if last_len + len(lines[i]) > max_batch_size:
            yield output
            last_len = 0
            output = []
        else:
            last_len += len(lines[i])
            output.append(lines[i])
            i += 1

    if output:
        yield output


def get_iam_token(oauth_token: str):
    """
    Get an IAM token from Yandex Translator API.

    Args:
        oauth_token (str): An OAuth token from Yandex Translator API.

    Returns:
        iam_token (str): An IAM token from Yandex Translator API.
    """
    response = requests.post(
        f"{get_settings().iam_api}/iam/v1/tokens",
        json={"yandexPassportOauthToken": oauth_token},
        timeout=15,
    )
    if response.status_code != 200:
        raise RuntimeError(
            f"Failed to get IAM token, status code {response.status_code}, text: {response.text}"
        )

    if not response.json() or "iamToken" not in response.json():
        raise RuntimeError("No IAM token returned")

    return response.json()["iamToken"]


def translate_batch(lines: list[str], iam_token: str, folder_id: str) -> list[str]:
    output: list[str] = []
    json_data = {
        "folderId": folder_id,
        "targetLanguageCode": "ru",
        "sourceLanguageCode": "en",
        "texts": lines,
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {iam_token}",
    }

    response = requests.post(
        f"{get_settings().translation_api}/translate/v2/translate",
        json=json_data,
        headers=headers,
        timeout=15,
    )

    if response.status_code != 200:
        raise TranslationError(
            f"Failed to translate line, status code {response.status_code}, text: {response.text}"
        )

    # Throws ValidationError when it fails
    model_response = YandexTranslatorResponse.model_validate_json(
        json.dumps(response.json())
    )
    for translation in model_response.translations:
        output.append(translation["text"])

    return output


def translate_lines(
    lines: list[str], settings: MachineTranslationSettings
) -> tuple[list[str], bool]:
    """
    Translate lines of text using machine translation.

    Args:
        lines: A list of strings to be translated.
        settings: An object containing machine translation settings.

    Returns:
        A list of translated strings.
    """
    # get IAM token first
    iam_token = get_iam_token(settings.oauth_token)

    # translate lines
    output: list[str] = []
    for batch in iterate_batches(lines):
        try:
            # TODO: make it in a smarter way, currently Yandex rejects
            # requests that are too frequent
            time.sleep(1.0 / 20.0)
            output += translate_batch(batch, iam_token, settings.folder_id)
        except TranslationError as e:
            logging.error("Translation error: %s", str(e))
            return output, True
        except ValidationError as e:
            logging.error("Validation error: %s", str(e))
            return output, True

    return output, False
