import logging
from unittest.mock import Mock, patch

import pytest

from app.settings import Settings
from app.translators import llm

# pylint: disable=C0116


@pytest.fixture(autouse=True)
def mock_llm_settings_autouse(monkeypatch):
    """Mock the settings to provide test values for LLM functionality."""
    # Mock the settings object with test values
    test_settings = Settings(
        llm_base_api="https://api.test.com/v4",
        llm_model="test-model",
        llm_base64_prompt=None,
    )

    # Mock the llm_prompt property to return the expected test prompt
    def mock_llm_prompt():
        return "You need to do the translation task from English to Russian. The prompt includes <context> section, <task> section, <glossary> section, <seg> tags, <term> tags, <orig> tags, and <trans> tags."

    # Replace the settings object and mock the llm_prompt property on the class
    monkeypatch.setattr("app.settings.settings", test_settings)
    monkeypatch.setattr(
        Settings, "llm_prompt", property(lambda self: mock_llm_prompt())
    )

    # Also need to mock the settings import in llm module
    monkeypatch.setattr("app.translators.llm.settings", test_settings)

    yield test_settings


def test_generate_prompt_prologue():
    """Test that prologue generates correct system prompt."""
    result = llm.generate_prompt_prologue()

    assert "You need to do the translation task from English to Russian." in result
    assert "<context>" in result
    assert "<task>" in result
    assert "<seg>" in result
    assert "<glossary>" in result
    assert "<term>" in result
    assert "<orig>" in result
    assert "<trans>" in result


def test_generate_prompt_ctx_middle_offset():
    """Test with offset in the middle"""
    lines = [(f"line{i}", []) for i in range(10)]

    result = llm.generate_prompt_ctx(lines, 5, 3)
    expected_lines = ["<seg>line2</seg>", "<seg>line3</seg>", "<seg>line4</seg>"]
    assert result == "<context>" + "\n".join(expected_lines) + "</context>"


def test_generate_prompt_ctx_beginning():
    """Test with offset at the beginning"""
    lines = [(f"line{i}", []) for i in range(10)]

    result = llm.generate_prompt_ctx(lines, 1, 3)
    expected_lines = ["<seg>line0</seg>"]
    assert result == "<context>" + "\n".join(expected_lines) + "</context>"


def test_generate_prompt_ctx_empty():
    """Test with no context"""
    lines = [(f"line{i}", []) for i in range(10)]

    result = llm.generate_prompt_ctx(lines, 0, 3)
    assert result == "<context></context>"


def test_generate_prompt_glossary():
    """Test glossary XML generation."""
    lines = [
        ("line1", [("hello", "привет"), ("world", "мир")]),
        ("line2", [("test", "тест"), ("hello", "привет")]),  # duplicate term
    ]

    result = llm.generate_prompt_glossary(lines)

    assert "<glossary>" in result
    assert "</glossary>" in result
    assert "<term><orig>hello</orig><trans>привет</trans></term>" in result
    assert "<term><orig>world</orig><trans>мир</trans></term>" in result
    assert "<term><orig>test</orig><trans>тест</trans></term>" in result
    # Should not have duplicates
    assert result.count("<term><orig>hello</orig><trans>привет</trans></term>") == 1


def test_generate_prompt_glossary_empty():
    """Test glossary generation with no glossary terms."""
    lines = [("line1", []), ("line2", [])]

    result = llm.generate_prompt_glossary(lines)

    assert result == "<glossary></glossary>"


def test_generate_prompt_task():
    """Test task XML generation."""
    lines = [("line1", []), ("line2", [])]

    result = llm.generate_prompt_task(lines)

    assert "<task>" in result
    assert "</task>" in result
    assert "<seg>line1</seg>" in result
    assert "<seg>line2</seg>" in result


def test_generate_prompt():
    """Test full prompt generation."""
    lines = [(f"line{i}", [("test", "тест")]) for i in range(10)]

    prompt, actual_size = llm.generate_prompt(lines, 5, 3, 2)

    assert "You need to do the translation task from English to Russian." in prompt
    # The prologue contains "<context>" text, so we expect 2 occurrences: one in prologue description, one in actual context
    assert prompt.count("<context>") == 2
    # The prologue contains "<task>" text, so we expect 2 occurrences: one in prologue description, one in actual task
    assert prompt.count("<task>") == 2
    # The prologue contains "<glossary>" text, so we expect 2 occurrences: one in prologue description, one in actual glossary
    assert prompt.count("<glossary>") == 2
    assert actual_size == 2

    # Check that task lines are correct
    assert "<seg>line5</seg>" in prompt
    assert "<seg>line6</seg>" in prompt
    assert "<seg>line7</seg>" not in prompt


def test_generate_prompt_ctx_negative_offset():
    """Test context generation with negative offset."""
    lines = [(f"line{i}", []) for i in range(5)]

    result = llm.generate_prompt_ctx(lines, -1, 3)

    # With negative offset, start becomes 0, so it includes all available lines
    expected_lines = [
        "<seg>line0</seg>",
        "<seg>line1</seg>",
        "<seg>line2</seg>",
        "<seg>line3</seg>",
    ]
    assert result == "<context>" + "\n".join(expected_lines) + "</context>"


def test_generate_prompt_ctx_large_context():
    """Test context generation when requested context is larger than available."""
    lines = [(f"line{i}", []) for i in range(3)]

    result = llm.generate_prompt_ctx(lines, 2, 10)

    # Should only include available lines before offset
    expected_lines = ["<seg>line0</seg>", "<seg>line1</seg>"]
    assert result == "<context>" + "\n".join(expected_lines) + "</context>"


def test_parse_lines_success():
    """Test successful parsing of LLM output."""
    network_out = (
        "<seg>translation1</seg>\n<seg>translation2</seg>\n<seg>translation3</seg>"
    )
    expected_size = 3

    result, success = llm.parse_lines(network_out, expected_size)

    assert success
    assert result == ["translation1", "translation2", "translation3"]


def test_parse_lines_wrong_number():
    """Test parsing when number of lines doesn't match expected."""
    network_out = "<seg>translation1</seg>\n<seg>translation2</seg>"
    expected_size = 3

    result, success = llm.parse_lines(network_out, expected_size)

    assert not success
    assert result == []


def test_parse_lines_invalid_format():
    """Test parsing when lines don't match expected format."""
    network_out = "invalid line\n<seg>translation2</seg>"
    expected_size = 2

    result, success = llm.parse_lines(network_out, expected_size)

    assert not success
    assert result == ["", "translation2"]


def test_parse_lines_empty_content():
    """Test parsing when seg content is empty."""
    network_out = "<seg></seg>\n<seg>translation2</seg>"
    expected_size = 2

    result, success = llm.parse_lines(network_out, expected_size)

    assert success
    assert result == ["", "translation2"]


@patch("app.translators.llm.OpenAI")
def test_translate_lines_success(mock_openai):
    """Test successful translation with mocked API."""
    # Mock the OpenAI client and response
    mock_client = Mock()
    mock_openai.return_value = mock_client

    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[
        0
    ].message.content = "<seg>translation1</seg>\n<seg>translation2</seg>"
    mock_client.chat.completions.create.return_value = mock_response

    lines = [("line1", []), ("line2", [])]

    result, has_error = llm.translate_lines(lines, "test_api_key")

    assert not has_error
    assert result == ["translation1", "translation2"]
    mock_openai.assert_called_once_with(
        api_key="test_api_key", base_url="https://api.test.com/v4", http_client=None
    )
    assert mock_client.chat.completions.create.call_count == 1


@patch("app.translators.llm.OpenAI")
def test_translate_lines_with_glossaries(mock_openai):
    """Test translation with glossary terms."""
    mock_client = Mock()
    mock_openai.return_value = mock_client

    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = "<seg>translation1</seg>"
    mock_client.chat.completions.create.return_value = mock_response

    lines = [("hello world", [("hello", "привет")])]

    result, has_error = llm.translate_lines(lines, "test_api_key")

    assert not has_error
    assert result == ["translation1"]

    # Check that glossary was included in the prompt
    call_args = mock_client.chat.completions.create.call_args
    prompt = call_args[1]["messages"][1]["content"]
    assert "<glossary>" in prompt
    assert "<term><orig>hello</orig><trans>привет</trans></term>" in prompt


@patch("app.translators.llm.OpenAI")
def test_translate_lines_api_error_retry(mock_openai, caplog):
    """Test translation with API error and retry logic."""
    mock_client = Mock()
    mock_openai.return_value = mock_client

    # First call fails, second succeeds
    mock_response_fail = Mock()
    mock_response_fail.choices = [Mock()]
    mock_response_fail.choices[0].message.content = "invalid output"

    mock_response_success = Mock()
    mock_response_success.choices = [Mock()]
    mock_response_success.choices[0].message.content = "<seg>translation1</seg>"

    mock_client.chat.completions.create.side_effect = [
        mock_response_fail,
        mock_response_success,
    ]

    lines = [("line1", [])]

    with caplog.at_level(logging.WARNING):
        result, has_error = llm.translate_lines(lines, "test_api_key")

    assert not has_error
    assert result == ["translation1"]
    assert mock_client.chat.completions.create.call_count == 2
    assert "Failed to get answer from LLM, attempt 1" in caplog.text


@patch("app.translators.llm.OpenAI")
def test_translate_lines_all_attempts_fail(mock_openai, caplog):
    """Test translation when all API attempts fail."""
    mock_client = Mock()
    mock_openai.return_value = mock_client

    # All calls return invalid output
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = "invalid output"
    mock_client.chat.completions.create.return_value = mock_response

    lines = [("line1", []), ("line2", [])]

    with caplog.at_level(logging.ERROR):
        result, has_error = llm.translate_lines(lines, "test_api_key")

    # Should return empty strings for all lines (task_size = 40)
    assert len(result) == 40  # 40 empty strings from task_size
    assert all(line == "" for line in result)  # All should be empty
    assert (
        not has_error
    )  # Note: llm.translate_lines returns False even when all attempts fail
    assert mock_client.chat.completions.create.call_count == 3  # 3 attempts
    assert "Was unable to get answer from LLM, returning empty list" in caplog.text


@patch("app.translators.llm.OpenAI")
def test_translate_lines_large_batch(mock_openai):
    """Test translation with large batch that gets split."""
    mock_client = Mock()
    mock_openai.return_value = mock_client

    # Create simple successful responses for each batch
    mock_response1 = Mock()
    mock_response1.choices = [Mock()]
    mock_response1.choices[0].message.content = "\n".join(
        [f"<seg>translation{i}</seg>" for i in range(40)]
    )

    mock_response2 = Mock()
    mock_response2.choices = [Mock()]
    mock_response2.choices[0].message.content = "\n".join(
        [f"<seg>translation{i}</seg>" for i in range(40)]
    )

    mock_response3 = Mock()
    mock_response3.choices = [Mock()]
    mock_response3.choices[0].message.content = "<seg>translation80</seg>"

    mock_client.chat.completions.create.side_effect = [
        mock_response1,
        mock_response2,
        mock_response3,
    ]

    # Create 81 lines (should be split into 3 batches: 40, 40, 1)
    lines = [(f"line{i}", []) for i in range(81)]

    result, has_error = llm.translate_lines(lines, "test_api_key")

    assert not has_error
    assert len(result) == 81
    assert mock_client.chat.completions.create.call_count == 3


@patch("app.translators.llm.OpenAI")
def test_translate_lines_empty_content(mock_openai):
    """Test translation when API returns None content."""
    mock_client = Mock()
    mock_openai.return_value = mock_client

    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = None
    mock_client.chat.completions.create.return_value = mock_response

    lines = [("line1", [])]

    result, has_error = llm.translate_lines(lines, "test_api_key")

    # Should handle None content gracefully - returns empty strings for all failed attempts
    assert not has_error
    assert len(result) == 40  # task_size = 40, all failed so 40 empty strings
    assert all(line == "" for line in result)  # All should be empty
    assert mock_client.chat.completions.create.call_count == 3  # Should retry 3 times


@patch("app.translators.llm.OpenAI")
def test_translate_lines_context_generation(mock_openai):
    """Test that context is properly included in the prompt."""
    mock_client = Mock()
    mock_openai.return_value = mock_client

    # Create simple successful response for the batch
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = "\n".join(
        [f"<seg>translation{i}</seg>" for i in range(10)]
    )
    mock_client.chat.completions.create.return_value = mock_response

    lines = [(f"line{i}", []) for i in range(10)]

    result, has_error = llm.translate_lines(lines, "test_api_key")

    assert not has_error
    assert len(result) == 10
    assert "translation0" in result

    # Check that context was included in the prompt
    call_args = mock_client.chat.completions.create.call_args
    prompt = call_args[1]["messages"][1]["content"]
    assert "<context>" in prompt
    # Should include previous lines as context
    assert "<seg>line0</seg>" in prompt
    assert "<seg>line1</seg>" in prompt
