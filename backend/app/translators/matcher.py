import logging
import re

import httpx
from openai import OpenAI

from app.formats.txt import extract_txt_content
from app.settings import settings

SYSTEM_PROMPT = (
    "You are a precise segment alignment tool. You will receive numbered English segments "
    "and numbered Russian segments from translated documents. Your task is to identify which "
    "Russian segment(s) correspond to each English segment.\n\n"
    "Rules:\n"
    "- Each English segment maps to one or more Russian segments (1-to-many).\n"
    "- Each English segment appears at most once in the response.\n"
    "- The same Russian segment can appear in multiple lines if it corresponds to multiple English segments.\n"
    "- Match based on semantic meaning — the Russian text is a translation/adaptation of the English.\n"
    "- If a segment has no match, omit it from the response.\n"
    "- Preserve document order — segments should appear in roughly ascending index order.\n\n"
    "Respond ONLY with alignment pairs in this exact format, one pair per line:\n"
    "[EN_INDEX] -> [RU_INDEX,RU_INDEX,...]\n\n"
    "Examples:\n"
    "[1] -> [1,2]\n"
    "[2] -> [3]\n"
    "[3] -> [5,6]\n"
    "[4] -> [7]"
)

ALIGNMENT_RE = re.compile(r"^\[(\d+)\]\s*->\s*\[([\d,]+)\]$")


def _parse_response(text: str) -> list[tuple[int, list[int]]]:
    results: list[tuple[int, list[int]]] = []
    for line in text.strip().splitlines():
        line = line.strip()
        m = ALIGNMENT_RE.match(line)
        if not m:
            logging.warning("Matcher: skipping unparseable line: %s", line)
            continue
        en_id = int(m.group(1))
        ru_ids = [int(x) for x in m.group(2).split(",") if x]
        if ru_ids:
            results.append((en_id, ru_ids))
    return results


def _build_user_prompt(en_segments: list[str], ru_segments: list[str]) -> str:
    en_lines = "\n".join(f"[{i + 1}] {seg}" for i, seg in enumerate(en_segments))
    ru_lines = "\n".join(f"[{i + 1}] {seg}" for i, seg in enumerate(ru_segments))
    return (
        f"<english_segments>\n{en_lines}\n</english_segments>\n\n"
        f"<russian_segments>\n{ru_lines}\n</russian_segments>"
    )


def match_segments_batch(
    en_segments: list[str],
    ru_segments: list[str],
    api_key: str,
) -> list[tuple[int, list[int]]]:
    if not settings.llm_base_api or not settings.llm_model:
        raise ValueError("No LLM base or LLM model configured")

    client = OpenAI(
        api_key=api_key,
        base_url=settings.llm_base_api,
        http_client=httpx.Client(proxy=settings.proxy_server)
        if settings.proxy_server
        else None,
    )

    prompt = _build_user_prompt(en_segments, ru_segments)

    for attempt in range(3):
        completion = client.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            extra_body={"thinking": {"type": "disabled"}},
        )
        content = completion.choices[0].message.content or ""
        parsed = _parse_response(content)
        if parsed:
            return parsed
        logging.warning("Matcher: empty response from LLM, attempt %d", attempt + 1)

    logging.error("Matcher: failed to get valid response after 3 attempts")
    return []


def match_all_segments(
    en_texts: list[str],
    ru_texts: list[str],
    api_key: str,
    batch_size: int = 50,
    ru_batch_size: int = 75,
    margin: int = 15,
) -> dict[int, list[int]]:
    result: dict[int, list[int]] = {}
    last_matched_ru = 0

    for batch_idx in range(0, len(en_texts), batch_size):
        en_batch = en_texts[batch_idx : batch_idx + batch_size]
        if not en_batch:
            break

        if batch_idx == 0:
            ru_start = 0
        else:
            ru_start = max(0, last_matched_ru - margin)

        ru_end = min(ru_start + ru_batch_size, len(ru_texts))
        ru_batch = ru_texts[ru_start:ru_end]

        if not ru_batch:
            break

        batch_result = match_segments_batch(en_batch, ru_batch, api_key)

        for en_idx, ru_indices in batch_result:
            global_en = en_idx - 1 + batch_idx
            global_ru = [idx - 1 + ru_start for idx in ru_indices]
            result[global_en] = global_ru

            if global_ru:
                last_matched_ru = max(last_matched_ru, max(global_ru) + 1)

    return result


def segment_russian_text(text: str) -> list[str]:
    txt_data = extract_txt_content(text)
    return [seg.original for seg in txt_data.segments]
