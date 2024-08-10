from app.formats.txt import extract_txt_content


def test_can_parse_simple_sentence():
    res = extract_txt_content("This is a sentence")
    assert len(res.segments) == 1
    assert res.segments[0].id_ == 1
    assert res.segments[0].original == "This is a sentence"
    assert not res.segments[0].translation
    assert res.segments[0].offset == 0


def test_can_parse_multiple_sentences():
    res = extract_txt_content(
        "This is the first sentence. This is the second. This is the third."
    )
    assert len(res.segments) == 3
    assert res.segments[0].id_ == 1
    assert res.segments[0].original == "This is the first sentence."
    assert not res.segments[0].translation
    assert res.segments[0].offset == 0

    assert res.segments[1].id_ == 2
    assert res.segments[1].original == "This is the second."
    assert not res.segments[1].translation
    assert res.segments[1].offset == len(res.segments[0].original) + 1

    assert res.segments[2].id_ == 3
    assert res.segments[2].original == "This is the third."
    assert not res.segments[2].translation
    assert (
        res.segments[2].offset
        == len(res.segments[0].original) + len(res.segments[1].original) + 2
    )


def test_can_parse_large_spaces():
    res = extract_txt_content("This is the first sentence.     This is the second.")
    assert len(res.segments) == 2
    assert res.segments[0].id_ == 1
    assert res.segments[0].original == "This is the first sentence."
    assert not res.segments[0].translation
    assert res.segments[0].offset == 0

    assert res.segments[1].id_ == 2
    assert res.segments[1].original == "This is the second."
    assert not res.segments[1].translation
    assert res.segments[1].offset == len(res.segments[0].original) + 5


def test_can_parse_multiline_string():
    data = """This is the first line\nThis is a second line."""
    res = extract_txt_content(data)
    assert len(res.segments) == 2

    assert res.segments[0].id_ == 1
    assert res.segments[0].original == "This is the first line"
    assert not res.segments[0].translation
    assert res.segments[0].offset == 0

    assert res.segments[1].id_ == 2
    assert res.segments[1].original == "This is a second line."
    assert not res.segments[1].translation
    assert res.segments[1].offset == len(res.segments[0].original) + 1


def test_can_parse_padded_line():
    data = """    Padded sentence.   """
    res = extract_txt_content(data)
    assert len(res.segments) == 1
    assert res.segments[0].id_ == 1
    assert res.segments[0].original == "Padded sentence."
    assert not res.segments[0].translation
    assert res.segments[0].offset == 4


def test_can_parse_windows_linebreaks():
    data = "This is the first line\r\nThis is a second line."
    res = extract_txt_content(data)
    assert len(res.segments) == 2
    assert res.segments[0].id_ == 1
    assert res.segments[0].original == "This is the first line"
    assert not res.segments[0].translation
    assert res.segments[0].offset == 0

    assert res.segments[1].id_ == 2
    assert res.segments[1].original == "This is a second line."
    assert not res.segments[1].translation
    assert res.segments[1].offset == len(res.segments[0].original) + 2


def test_can_update_segment():
    data = """This is the line"""
    res = extract_txt_content(data)

    res.segments[0].translation = "This is the translated line"

    res.commit()
    file = res.write()
    assert file.read().decode() == """This is the translated line"""


def test_segment_update_stores_spaces():
    data = """This is the sentence.    This is another sentence."""
    res = extract_txt_content(data)

    res.segments[0].translation = "This is the translated sentence."
    res.segments[1].translation = "This is another translated sentence."

    res.commit()
    file = res.write()
    assert (
        file.read().decode()
        == """This is the translated sentence.    This is another translated sentence."""
    )


def test_segment_update_stores_newlines():
    data = """This is the first line.    This is a second line.
  This is a third line.
    """
    res = extract_txt_content(data)

    res.segments[0].translation = "This is the translated first line."
    res.segments[1].translation = "This is another translated sentence."
    res.segments[2].translation = "This is a third translated sentence."

    res.commit()
    file = res.write()
    assert (
        file.read().decode()
        == """This is the translated first line.    This is another translated sentence.
  This is a third translated sentence.
    """
    )


def test_missing_translation_segments_are_skipped():
    data = """This is the first sentence.    This is a second sentence."""
    res = extract_txt_content(data)

    res.segments[0].translation = None
    res.segments[1].translation = "This is another translated sentence."

    res.commit()
    file = res.write()
    assert (
        file.read().decode()
        == """This is the first sentence.    This is another translated sentence."""
    )
