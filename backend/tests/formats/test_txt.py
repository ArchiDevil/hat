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
