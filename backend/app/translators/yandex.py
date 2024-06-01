import logging
from typing import Generator

from pydantic import BaseModel, PositiveInt
import requests

from app.models import MachineTranslationSettings
from app.settings import Settings


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
    response = requests.post(
        f"{Settings.translation_api}/iam/v1/tokens",
        json={"yandexPassportOauthToken": settings.oauth_token},
        timeout=15,
    )
    if response.status_code != 200:
        logging.error("%s %s", response.status_code, response.text)
        raise RuntimeError("Failed to get IAM token")

    if not response.json() or "iamToken" not in response.json():
        logging.error("No IAM token returned")
        raise RuntimeError("No IAM token returned")

    iam_token = response.json()["iamToken"]

    # translate lines
    output: list[str] = []
    for batch in iterate_batches(lines):
        json_data = {
            "folderId": settings.folder_id,
            "targetLanguageCode": "ru",
            "sourceLanguageCode": "en",
            "texts": batch,
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {iam_token}",
        }

        response = requests.post(
            f"{Settings.translation_api}/translate/v2/translate",
            json=json_data,
            headers=headers,
            timeout=15,
        )

        if response.status_code != 200:
            logging.error("%s %s", response.status_code, response.text)
            raise RuntimeError("Failed to translate line")

        model_response = YandexTranslatorResponse.model_validate_json(response.json())
        for translation in model_response.translations:
            output += translation["text"]

    return output
