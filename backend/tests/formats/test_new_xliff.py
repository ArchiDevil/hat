from app.formats.xliff import XliffNewFile, XliffSegment


def test_can_create_empty_xliff():
    data = XliffNewFile([], "test").serialize()
    content = data.read()
    assert b"xml" in content
    assert b"<body/>" in content


def test_can_create_xliff_with_single_segment():
    segment = XliffSegment(1, False, "Hello", "", None)
    data = XliffNewFile([segment], "test.txt").serialize()
    content = data.read()
    assert b"<trans-unit" in content
    assert b'id="1"' in content
    assert b'approved="no"' in content
    assert b"<source" in content
    assert b"Hello" in content
    assert b"<target" in content


def test_can_create_xliff_with_multiple_segments():
    segments = [
        XliffSegment(1, False, "Hello", "", None),
        XliffSegment(2, False, "World", "", None),
        XliffSegment(3, False, "Test", "", None),
    ]
    data = XliffNewFile(segments, "test.txt").serialize()
    content = data.read()
    assert b'id="1"' in content
    assert b'id="2"' in content
    assert b'id="3"' in content
    assert b"Hello" in content
    assert b"World" in content
    assert b"Test" in content


def test_xliff_contains_required_elements():
    segment = XliffSegment(1, False, "Hello", "", None)
    data = XliffNewFile([segment], "test.txt").serialize()
    content = data.read()
    assert b"<xliff" in content
    assert b'version="1.2"' in content
    assert b"<file" in content
    assert b"<header>" in content
    assert b"<tool" in content
    assert b"<body>" in content


def test_xliff_contains_tool_information():
    segment = XliffSegment(1, False, "Hello", "", None)
    data = XliffNewFile([segment], "test.txt").serialize()
    content = data.read()
    assert b'tool-name="Human Assisted Translator"' in content
    assert b'tool-id="5ae5ad5c-6d82-41a8-a653-ba96b6f8eb01"' in content
    assert b'tool-version="0.9"' in content


def test_xliff_contains_original_filename():
    segment = XliffSegment(1, False, "Hello", "", None)
    data = XliffNewFile([segment], "my_document.txt").serialize()
    content = data.read()
    assert b'original="my_document.txt"' in content


def test_xliff_contains_source_and_target_languages():
    segment = XliffSegment(1, False, "Hello", "", None)
    data = XliffNewFile([segment], "test.txt").serialize()
    content = data.read()
    assert b'source-language="en"' in content
    assert b'target-language="ru"' in content


def test_xliff_contains_datatype():
    segment = XliffSegment(1, False, "Hello", "", None)
    data = XliffNewFile([segment], "test.txt").serialize()
    content = data.read()
    assert b'datatype="plaintext"' in content


def test_xliff_contains_date():
    segment = XliffSegment(1, False, "Hello", "", None)
    data = XliffNewFile([segment], "test.txt").serialize()
    content = data.read()
    assert b"date=" in content


def test_segment_with_translation():
    segment = XliffSegment(1, False, "Hello", "Привет", "translated")
    data = XliffNewFile([segment], "test.txt").serialize()
    content = data.read()
    assert "Привет".encode() in content
    assert b"<target" in content
    assert b'state="translated"' in content


def test_segment_without_translation():
    segment = XliffSegment(1, False, "Hello", "", None)
    data = XliffNewFile([segment], "test.txt").serialize()
    content = data.read()
    assert b"<target" in content
    assert b'state="new"' in content


def test_approved_segment():
    segment = XliffSegment(1, True, "Hello", "Привет", None)
    data = XliffNewFile([segment], "test.txt").serialize()
    content = data.read()
    assert b'approved="yes"' in content


def test_unapproved_segment():
    segment = XliffSegment(1, False, "Hello", "Привет", None)
    data = XliffNewFile([segment], "test.txt").serialize()
    content = data.read()
    assert b'approved="no"' in content


def test_segment_with_needs_translation_state():
    segment = XliffSegment(1, False, "Hello", "", "needs-translation")
    data = XliffNewFile([segment], "test.txt").serialize()
    content = data.read()
    assert b'state="needs-translation"' in content


def test_segment_with_translated_state():
    segment = XliffSegment(1, False, "Hello", "Привет", "translated")
    data = XliffNewFile([segment], "test.txt").serialize()
    content = data.read()
    assert b'state="translated"' in content


def test_segment_with_final_state():
    segment = XliffSegment(1, False, "Hello", "Привет", "final")
    data = XliffNewFile([segment], "test.txt").serialize()
    content = data.read()
    assert b'state="final"' in content


def test_segment_with_needs_review_translation_state():
    segment = XliffSegment(1, False, "Hello", "Привет", "needs-review-translation")
    data = XliffNewFile([segment], "test.txt").serialize()
    content = data.read()
    assert b'state="needs-review-translation"' in content


def test_segment_with_signed_off_state():
    segment = XliffSegment(1, False, "Hello", "Привет", "signed-off")
    data = XliffNewFile([segment], "test.txt").serialize()
    content = data.read()
    assert b'state="signed-off"' in content


def test_segment_with_needs_adaptation_state():
    segment = XliffSegment(1, False, "Hello", "Привет", "needs-adaptation")
    data = XliffNewFile([segment], "test.txt").serialize()
    content = data.read()
    assert b'state="needs-adaptation"' in content


def test_segment_with_needs_l10n_state():
    segment = XliffSegment(1, False, "Hello", "Привет", "needs-l10n")
    data = XliffNewFile([segment], "test.txt").serialize()
    content = data.read()
    assert b'state="needs-l10n"' in content


def test_segment_with_needs_review_adaptation_state():
    segment = XliffSegment(1, False, "Hello", "Привет", "needs-review-adaptation")
    data = XliffNewFile([segment], "test.txt").serialize()
    content = data.read()
    assert b'state="needs-review-adaptation"' in content


def test_segment_with_needs_review_l10n_state():
    segment = XliffSegment(1, False, "Hello", "Привет", "needs-review-l10n")
    data = XliffNewFile([segment], "test.txt").serialize()
    content = data.read()
    assert b'state="needs-review-l10n"' in content


def test_source_has_xml_space_preserve():
    segment = XliffSegment(1, False, "Hello", "", None)
    data = XliffNewFile([segment], "test.txt").serialize()
    content = data.read()
    assert b"<source" in content
    assert b'xml:space="preserve"' in content


def test_target_has_xml_space_preserve():
    segment = XliffSegment(1, False, "Hello", "", None)
    data = XliffNewFile([segment], "test.txt").serialize()
    content = data.read()
    assert b"<target" in content
    assert b'xml:space="preserve"' in content


def test_xliff_has_xml_declaration():
    segment = XliffSegment(1, False, "Hello", "", None)
    data = XliffNewFile([segment], "test.txt").serialize()
    content = data.read()
    assert b"<?xml version='1.0'" in content
    assert b"encoding='utf-8'" in content


def test_xliff_has_correct_namespace():
    segment = XliffSegment(1, False, "Hello", "", None)
    data = XliffNewFile([segment], "test.txt").serialize()
    content = data.read()
    assert b'xmlns="urn:oasis:names:tc:xliff:document:1.2"' in content


def test_segment_with_special_characters_in_source():
    segment = XliffSegment(1, False, "Hello & World <test>", "", None)
    data = XliffNewFile([segment], "test.txt").serialize()
    content = data.read()
    assert b"Hello" in content
    assert b"World" in content


def test_segment_with_special_characters_in_target():
    segment = XliffSegment(1, False, "Hello", "Привет & Мир <тест>", None)
    data = XliffNewFile([segment], "test.txt").serialize()
    content = data.read()
    assert "Привет".encode() in content
    assert "Мир".encode() in content


def test_segment_with_empty_source():
    segment = XliffSegment(1, False, "", "", None)
    data = XliffNewFile([segment], "test.txt").serialize()
    content = data.read()
    assert b"<source" in content
    assert b"<target" in content


def test_segment_with_multiline_text():
    segment = XliffSegment(
        1, False, "Line 1\nLine 2\nLine 3", "Строка 1\nСтрока 2\nСтрока 3", None
    )
    data = XliffNewFile([segment], "test.txt").serialize()
    content = data.read()
    assert b"Line 1" in content
    assert b"Line 2" in content
    assert b"Line 3" in content
    assert "Строка 1".encode() in content
    assert "Строка 2".encode() in content
    assert "Строка 3".encode() in content


def test_multiple_segments_with_different_states():
    segments = [
        XliffSegment(1, False, "Hello", "", "needs-translation"),
        XliffSegment(2, True, "World", "Мир", "translated"),
        XliffSegment(3, False, "Test", "", "new"),
    ]
    data = XliffNewFile(segments, "test.txt").serialize()
    content = data.read()
    assert b'state="needs-translation"' in content
    assert b'state="translated"' in content
    assert b'state="new"' in content
    assert b'approved="yes"' in content
    assert b'approved="no"' in content


def test_multiple_segments_with_mixed_approval():
    segments = [
        XliffSegment(1, True, "Hello", "Привет", None),
        XliffSegment(2, False, "World", "", None),
        XliffSegment(3, True, "Test", "Тест", None),
    ]
    data = XliffNewFile(segments, "test.txt").serialize()
    content = data.read()
    assert b'id="1"' in content
    assert b'approved="yes"' in content
    assert b'id="2"' in content
    assert b'approved="no"' in content
    assert b'id="3"' in content
    assert b'approved="yes"' in content
