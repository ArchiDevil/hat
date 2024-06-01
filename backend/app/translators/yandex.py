import json
import logging
from typing import Generator

from pydantic import BaseModel, PositiveInt
import requests

from app.models import MachineTranslationSettings
from app.settings import get_settings


class YandexTranslatorResponse(BaseModel):
    """
    A response object from Yandex Translator API.

    Attributes:
        translations (list[dict]): A list of translation results.
    """

    translations: list[dict[str, str]]


def iterate_batches(
    lines: list[str], batch_size: PositiveInt = 256
) -> Generator[list[str], None, None]:
    for i in range(0, len(lines), batch_size):
        yield lines[i : min(len(lines), i + batch_size)]


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
        logging.error("%s %s", response.status_code, response.text)
        raise RuntimeError("Failed to get IAM token")

    if not response.json() or "iamToken" not in response.json():
        logging.error("No IAM token returned")
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

    # TODO: it is better to return what we have translated already to
    # avoid losing user's money when the error happens in the middle
    # of the translation process
    # or try again couple of times
    if response.status_code != 200:
        logging.error("%s %s", response.status_code, response.text)
        raise RuntimeError("Failed to translate line")

    model_response = YandexTranslatorResponse.model_validate_json(
        json.dumps(response.json())
    )
    for translation in model_response.translations:
        output.append(translation["text"])

    return output


def translate_lines(
    lines: list[str], settings: MachineTranslationSettings
) -> list[str]:
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
        output += translate_batch(batch, iam_token, settings.folder_id)

    return output
