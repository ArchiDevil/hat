# This is a great idea to make a universal translator using OpenAI API, instead
# of specific translators for every service, but this will require much effort
# to prepare and manage a library of prompts for every context size, so it is
# postponed for the future.

import logging
import re

import httpx
from openai import OpenAI

from app.settings import settings
from app.translators.common import LineWithGlossaries


def generate_prompt_prologue() -> str:
    if not settings.llm_prompt:
        logging.error("No LLM prompt configured")
    return settings.llm_prompt


def generate_prompt_ctx(
    lines: list[LineWithGlossaries], offset: int, ctx_size: int
) -> str:
    start = max(offset - ctx_size, 0)
    ctx_lines = [f"<seg>{line[0]}</seg>" for line in lines[start:offset]]
    return f"<context>{'\n'.join(ctx_lines)}</context>"


def generate_prompt_glossary(lines: list[LineWithGlossaries]) -> str:
    terms = {}
    for _, glossary_term in lines:
        for original, translation in glossary_term:
            terms[original] = (
                f"<term><orig>{original}</orig><trans>{translation}</trans></term>"
            )

    return f"<glossary>{'\n'.join(terms.values())}</glossary>"


def generate_prompt_task(lines: list[LineWithGlossaries]) -> str:
    segments = [f"<seg>{line[0]}</seg>" for line in lines]
    return f"<task>{'\n'.join(segments)}</task>"


def generate_prompt(
    lines: list[LineWithGlossaries], offset: int, ctx_size: int, task_size: int
) -> tuple[str, int]:
    task_lines = lines[offset : offset + task_size]
    parts = [
        generate_prompt_prologue(),
        generate_prompt_ctx(lines, offset, ctx_size),
        generate_prompt_glossary(task_lines),
        generate_prompt_task(task_lines),
    ]
    return "\n\n".join(parts), len(task_lines)


SEG_MATCHER = re.compile(r"<seg>(.*)</seg>")


def parse_lines(network_out: str, expected_size: int) -> tuple[list[str], bool]:
    output: list[str] = []

    split = network_out.strip().splitlines()
    if len(split) != expected_size:
        logging.warning("Unexpected LLM output, not enough lines returned %s", split)
        return [], False

    failed = False
    for line in split:
        m = re.match(SEG_MATCHER, line)
        if not m:
            logging.warning("Unexpected LLM output, no match found in %s", line)
            output.append("")
            failed = True
            continue
        output.append(m.group(1))

    return output, not failed


def translate_lines(
    lines: list[LineWithGlossaries], api_key: str
) -> tuple[list[str], bool]:
    """
    Translate lines of text using LLM translation.

    Args:
        lines: A list of strings to be translated.
        settings: An object containing LLM translation settings.

    Returns:
        A list of translated strings.
    """
    # when settings are not set, it fails immediately
    if not settings.llm_base_api or not settings.llm_model:
        logging.error(
            "No LLM base or LLM model configured. LLM base: %s, LLM model: %s",
            settings.llm_base_api,
            settings.llm_model,
        )
        return [], True

    client = OpenAI(
        api_key=api_key,
        base_url=settings.llm_base_api,
        http_client=httpx.Client(proxy=settings.proxy_server)
        if settings.proxy_server
        else None,
    )

    output: list[str] = []

    task_size = 40
    ctx_size = 40
    for offset in range(0, len(lines), task_size):
        for attempt in range(3):
            prompt, actual_size = generate_prompt(lines, offset, ctx_size, task_size)
            completion = client.chat.completions.create(
                model=settings.llm_model,
                messages=[
                    {
                        "role": "system",
                        # TODO: make it configurable
                        "content": "You are a smart translator from English to Russian.",
                    },
                    {"role": "user", "content": prompt},
                ],
                extra_body={"thinking": {"type": "disabled"}},
            )
            # parse output of the network
            batch_lines, result = parse_lines(
                completion.choices[0].message.content or "", actual_size
            )
            if result:
                output += batch_lines
                break
            logging.warning("Failed to get answer from LLM, attempt %s", attempt + 1)
        else:
            logging.error("Was unable to get answer from LLM, returning empty list")
            for _ in range(task_size):
                output.append("")

    return output, False
