import json
import logging
import time
from typing import Generator

import requests
from pydantic import BaseModel, PositiveInt, ValidationError

from app.settings import settings
from app.translators.common import LineWithGlossaries, TranslationError


class YandexTranslatorResponse(BaseModel):
    """
    A response object from Yandex Translator API.

    Attributes:
        translations (list[dict]): A list of translation results.
    """

    translations: list[dict[str, str]]


# Currently Yandex rejects requests larger than 10k symbols and more than
# 50 records in glossary.
def iterate_batches(
    lines: list[LineWithGlossaries],
    max_symbols_per_batch: PositiveInt = 10000,
    max_glossaries_per_batch: PositiveInt = 50,
) -> Generator[list[LineWithGlossaries], None, None]:
    output_lines: list[LineWithGlossaries] = []
    last_symbols_len = 0
    last_glossaries_len = 0
    i = 0
    while i < len(lines):
        # special case for first large glossary list
        if not output_lines and len(lines[i][1]) > max_glossaries_per_batch:
            last_symbols_len = len(lines[i][0])
            last_glossaries_len = 50
            output_lines.append((lines[i][0], lines[i][1][:max_glossaries_per_batch]))
            i += 1
            continue

        if (
            last_symbols_len + len(lines[i][0]) > max_symbols_per_batch
            or last_glossaries_len + len(lines[i][1]) > max_glossaries_per_batch
        ):
            yield output_lines
            last_symbols_len = 0
            last_glossaries_len = 0
            output_lines = []
        else:
            last_symbols_len += len(lines[i][0])
            last_glossaries_len += len(lines[i][1])
            output_lines.append(lines[i])
            i += 1

    if output_lines:
        yield output_lines


def get_iam_token(oauth_token: str):
    """
    Get an IAM token from Yandex Translator API.

    Args:
        oauth_token (str): An OAuth token from Yandex Translator API.

    Returns:
        iam_token (str): An IAM token from Yandex Translator API.
    """
    response = requests.post(
        f"{settings.iam_api}/iam/v1/tokens",
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


def translate_batch(
    lines: list[LineWithGlossaries],
    iam_token: str,
    folder_id: str,
) -> list[str]:
    output: list[str] = []
    json_data = {
        "folderId": folder_id,
        "targetLanguageCode": "ru",
        "sourceLanguageCode": "en",
        "texts": [line for line, _ in lines],
    }

    glossary_data = {"glossaryData": {"glossaryPairs": []}}
    for _, glossaries in lines:
        for glossary in glossaries:
            glossary_data["glossaryData"]["glossaryPairs"].append(
                {
                    "sourceText": glossary[0],
                    "translatedText": glossary[1],
                }
            )
    if glossary_data["glossaryData"]["glossaryPairs"]:
        json_data["glossaryConfig"] = glossary_data

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {iam_token}",
    }

    response = requests.post(
        f"{settings.translation_api}/translate/v2/translate",
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
    lines: list[LineWithGlossaries], oauth_token: str, folder_id: str
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
    iam_token = get_iam_token(oauth_token)

    # translate lines
    output: list[str] = []
    for batch in iterate_batches(lines):
        try:
            # TODO: make it in a smarter way, currently Yandex rejects
            # requests that are too frequent
            time.sleep(1.0 / 20.0)
            output += translate_batch(batch, iam_token, folder_id)
        except TranslationError as e:
            logging.error("Translation error: %s", str(e))
            return output, True
        except ValidationError as e:
            logging.error("Validation error: %s", str(e))
            return output, True

    return output, False
