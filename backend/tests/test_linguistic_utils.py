from app.linguistic.utils import postprocess_stemmed_segment, stem_sentence


def test_possessive_words():
    # The exact stemmed output depends on the SnowballStemmer
    result = postprocess_stemmed_segment(stem_sentence("The teacher's book"))
    # Should stem "teacher" and keep other tokens
    assert "teacher" in " ".join(result) or "teach" in " ".join(result)
    assert "'" not in " ".join(result)  # Apostrophes should be removed from possessives


def test_plural_possessive():
    result = postprocess_stemmed_segment(stem_sentence("The students' classroom"))
    assert "student" in " ".join(result) or "student" in result
    assert "'" not in " ".join(result)  # Apostrophes should be removed


def test_some_contractions_unchanged():
    """Test that contractions are not modified."""
    result = postprocess_stemmed_segment(stem_sentence("I don't like it"))
    # "don't" gets tokenized as ["do", "n't"], both should be processed
    assert "do" in result
    assert "n't" in result


def test_apostrophes_remapping():
    """Test that different Unicode apostrophes are ignored too."""
    result = postprocess_stemmed_segment(
        stem_sentence(
            "Teacher\u2018s thing, teacher\u2019s thing, teacher\u201bs thing"
        )
    )
    assert "'" not in " ".join(result)
