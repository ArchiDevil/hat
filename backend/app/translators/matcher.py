import logging
import re

import httpx
from openai import OpenAI

from app.formats.txt import extract_txt_content
from app.settings import settings

ALIGNMENT_RE = re.compile(r"^\[(\d+)\]\s*->\s*\[([\d,]+)\]$")


def _parse_response(text: str) -> list[tuple[int, list[int]]]:
    results: list[tuple[int, list[int]]] = []
    for line in text.strip().splitlines():
        line = line.strip()
        m = ALIGNMENT_RE.match(line)
        if not m:
            logging.warning("Matcher: skipping unparseable line: %s", line)
            continue
        orig_id = int(m.group(1))
        match_ids = [int(x) for x in m.group(2).split(",") if x]
        if match_ids:
            results.append((orig_id, match_ids))
    return results


def _build_user_prompt(orig_segments: list[str], match_segments: list[str]) -> str:
    orig_lines = "\n".join(f"[{i + 1}] {seg}" for i, seg in enumerate(orig_segments))
    match_lines = "\n".join(f"[{i + 1}] {seg}" for i, seg in enumerate(match_segments))
    return (
        f"<english_segments>\n{orig_lines}\n</english_segments>\n\n"
        f"<russian_segments>\n{match_lines}\n</russian_segments>"
    )


def match_segments_batch(
    original_segments: list[str],
    to_match_segments: list[str],
    api_key: str,
) -> list[tuple[int, list[int]]]:
    if not settings.llm_base_api or not settings.llm_model:
        raise ValueError("No LLM base or LLM model configured")

    if not settings.llm_match_prompt:
        raise ValueError("No LLM match prompt configured")

    client = OpenAI(
        api_key=api_key,
        base_url=settings.llm_base_api,
        http_client=httpx.Client(proxy=settings.proxy_server)
        if settings.proxy_server
        else None,
    )

    prompt = _build_user_prompt(original_segments, to_match_segments)

    for attempt in range(3):
        completion = client.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {"role": "system", "content": settings.llm_match_prompt},
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
    original_texts: list[str],
    to_match_texts: list[str],
    api_key: str,
    batch_size: int = 50,
    match_batch_size: int = 75,
    margin: int = 15,
) -> dict[int, list[int]]:
    result: dict[int, list[int]] = {}
    last_matched_idx = 0

    for batch_idx in range(0, len(original_texts), batch_size):
        orig_batch = original_texts[batch_idx : batch_idx + batch_size]
        if not orig_batch:
            break

        if batch_idx == 0:
            match_start = 0
        else:
            match_start = max(0, last_matched_idx - margin)

        match_end = min(match_start + match_batch_size, len(to_match_texts))
        match_batch = to_match_texts[match_start:match_end]

        if not match_batch:
            break

        batch_result = match_segments_batch(orig_batch, match_batch, api_key)

        for orig_idx, match_indices in batch_result:
            global_orig = orig_idx - 1 + batch_idx
            global_match = [idx - 1 + match_start for idx in match_indices]
            result[global_orig] = global_match

            if global_match:
                last_matched_idx = max(last_matched_idx, max(global_match) + 1)

    return result


def segment_text_to_match(text: str) -> list[str]:
    txt_data = extract_txt_content(text)
    return [seg.original for seg in txt_data.segments]
