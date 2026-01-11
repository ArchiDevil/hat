from app.linguistic.word_count import count_words


def test_simple_sentence():
    """Test counting words in a simple sentence."""
    assert count_words("Hello world") == 2
    assert count_words("This is a test") == 4


def test_empty_string():
    """Test that empty string returns 0."""
    assert count_words("") == 0
    assert count_words("   ") == 0
    assert count_words("\t\n") == 0


def test_single_word():
    """Test counting a single word."""
    assert count_words("Hello") == 1
    assert count_words("word") == 1


def test_multiple_spaces():
    """Test that multiple spaces are handled correctly."""
    assert count_words("Hello    world") == 2
    assert count_words("This  is  a  test") == 4


def test_leading_trailing_whitespace():
    """Test that leading and trailing whitespace are handled."""
    assert count_words("  Hello world  ") == 2
    assert count_words("\tTest\t") == 1


def test_punctuation():
    """Test that punctuation doesn't affect word count."""
    assert count_words("Hello, world!") == 2
    assert count_words("This is a test.") == 4


def test_numbers():
    """Test that numbers are counted as words."""
    assert count_words("123") == 1
    assert count_words("There are 123 items") == 4


def test_mixed_content():
    """Test mixed content with various characters."""
    assert count_words("Hello, world! This is test #123.") == 6


def test_unicode():
    """Test that unicode characters are handled."""
    assert count_words("Hello 世界") == 2
    assert count_words("Привет мир") == 2


def test_newlines_and_tabs():
    """Test that newlines and tabs are treated as whitespace."""
    assert count_words("Hello\nworld") == 2
    assert count_words("Hello\tworld") == 2
    assert count_words("Hello\n\tworld") == 2


def test_consecutive_whitespace():
    """Test that consecutive whitespace is handled."""
    assert count_words("Hello   \n\t   world") == 2
