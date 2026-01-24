"""Tests for document utility functions."""

import json

import pytest

from app.documents.utils import apply_diff, compute_diff


class TestComputeDiff:
    """Tests for compute_diff function."""

    def test_empty_strings(self):
        """Test diff between empty strings."""
        diff = compute_diff("", "")
        diff_data = json.loads(diff)
        assert "ops" in diff_data
        assert "old_len" in diff_data
        assert diff_data["old_len"] == 0

    def test_identical_strings(self):
        """Test diff between identical strings."""
        diff = compute_diff("Hello World", "Hello World")
        diff_data = json.loads(diff)
        assert "ops" in diff_data
        assert len(diff_data["ops"]) == 1
        assert diff_data["ops"][0] == ["equal", 0, 11]
        assert "old_len" in diff_data

    def test_simple_replacement(self):
        """Test diff with simple replacement."""
        old = "Hello World"
        new = "Hello Beautiful World"
        diff = compute_diff(old, new)

        # Verify diff is valid JSON
        diff_data = json.loads(diff)
        assert "ops" in diff_data
        assert "old_len" in diff_data
        assert diff_data["old_len"] == len(old)

        # Verify reconstruction works
        reconstructed = apply_diff(old, diff)
        assert reconstructed == new

    def test_simple_deletion(self):
        """Test diff with simple deletion."""
        old = "Hello Beautiful World"
        new = "Hello World"
        diff = compute_diff(old, new)

        # Verify diff is valid JSON
        diff_data = json.loads(diff)
        assert "ops" in diff_data
        assert diff_data["old_len"] == len(old)

        # Verify reconstruction works
        reconstructed = apply_diff(old, diff)
        assert reconstructed == new

    def test_simple_insertion(self):
        """Test diff with simple insertion."""
        old = "Hello World"
        new = "Hello Amazing World"
        diff = compute_diff(old, new)

        # Verify diff is valid JSON
        diff_data = json.loads(diff)
        assert "ops" in diff_data
        assert diff_data["old_len"] == len(old)

        # Verify reconstruction works
        reconstructed = apply_diff(old, diff)
        assert reconstructed == new

    def test_complex_changes(self):
        """Test diff with multiple types of changes."""
        old = "The quick brown fox jumps over the lazy dog"
        new = "A fast brown fox leaps over the sleeping dog"
        diff = compute_diff(old, new)

        # Verify diff is valid JSON
        diff_data = json.loads(diff)
        assert "ops" in diff_data
        assert diff_data["old_len"] == len(old)

        # Verify reconstruction works
        reconstructed = apply_diff(old, diff)
        assert reconstructed == new

    def test_unicode_characters(self):
        """Test diff with unicode characters."""
        old = "Привет мир"
        new = "Привет прекрасный мир"
        diff = compute_diff(old, new)

        # Verify diff is valid JSON
        diff_data = json.loads(diff)
        assert "ops" in diff_data
        assert diff_data["old_len"] == len(old)

        # Verify reconstruction works
        reconstructed = apply_diff(old, diff)
        assert reconstructed == new

    def test_multiline_text(self):
        """Test diff with multiline text."""
        old = "Line 1\nLine 2\nLine 3"
        new = "Line 1\nModified Line 2\nLine 3"
        diff = compute_diff(old, new)

        # Verify diff is valid JSON
        diff_data = json.loads(diff)
        assert "ops" in diff_data
        assert diff_data["old_len"] == len(old)

        # Verify reconstruction works
        reconstructed = apply_diff(old, diff)
        assert reconstructed == new

    def test_empty_to_nonempty(self):
        """Test diff from empty to non-empty string."""
        old = ""
        new = "New text"
        diff = compute_diff(old, new)

        # Verify diff is valid JSON
        diff_data = json.loads(diff)
        assert "ops" in diff_data
        assert diff_data["old_len"] == 0

        # Verify reconstruction works
        reconstructed = apply_diff(old, diff)
        assert reconstructed == new

    def test_nonempty_to_empty(self):
        """Test diff from non-empty to empty string."""
        old = "Old text"
        new = ""
        diff = compute_diff(old, new)

        # Verify diff is valid JSON
        diff_data = json.loads(diff)
        assert "ops" in diff_data
        assert diff_data["old_len"] == len(old)

        # Verify reconstruction works
        reconstructed = apply_diff(old, diff)
        assert reconstructed == new

    def test_special_characters(self):
        """Test diff with special characters."""
        old = "Hello & goodbye"
        new = "Hello <world> goodbye"
        diff = compute_diff(old, new)

        # Verify diff is valid JSON
        diff_data = json.loads(diff)
        assert "ops" in diff_data
        assert diff_data["old_len"] == len(old)

        # Verify reconstruction works
        reconstructed = apply_diff(old, diff)
        assert reconstructed == new

    def test_whitespace_changes(self):
        """Test diff with whitespace changes."""
        old = "Hello   World"
        new = "Hello World"
        diff = compute_diff(old, new)

        # Verify diff is valid JSON
        diff_data = json.loads(diff)
        assert "ops" in diff_data
        assert diff_data["old_len"] == len(old)

        # Verify reconstruction works
        reconstructed = apply_diff(old, diff)
        assert reconstructed == new


class TestApplyDiff:
    """Tests for apply_diff function."""

    def test_empty_diff(self):
        """Test applying empty diff."""
        old = "Hello World"
        diff = ""
        result = apply_diff(old, diff)
        assert result == old

    def test_equal_opcode(self):
        """Test applying diff with equal opcodes."""
        old = "Hello World"
        new = "Hello World"
        diff = compute_diff(old, new)
        result = apply_diff(old, diff)
        assert result == new

    def test_replace_opcode(self):
        """Test applying diff with replace opcode."""
        old = "Hello World"
        new = "Hello Beautiful World"
        diff = compute_diff(old, new)
        result = apply_diff(old, diff)
        assert result == new

    def test_delete_opcode(self):
        """Test applying diff with delete opcode."""
        old = "Hello Beautiful World"
        new = "Hello World"
        diff = compute_diff(old, new)
        result = apply_diff(old, diff)
        assert result == new

    def test_insert_opcode(self):
        """Test applying diff with insert opcode."""
        old = "Hello World"
        new = "Hello Amazing World"
        diff = compute_diff(old, new)
        result = apply_diff(old, diff)
        assert result == new

    def test_multiple_opcodes(self):
        """Test applying diff with multiple opcodes."""
        old = "The quick brown fox"
        new = "A fast brown dog"
        diff = compute_diff(old, new)
        result = apply_diff(old, diff)
        assert result == new

    def test_empty_old_text(self):
        """Test applying diff to empty old text."""
        old = ""
        new = "New text"
        diff = compute_diff(old, new)
        result = apply_diff(old, diff)
        assert result == new

    def test_result_empty(self):
        """Test applying diff that results in empty string."""
        old = "Old text"
        new = ""
        diff = compute_diff(old, new)
        result = apply_diff(old, diff)
        assert result == new
        assert result == ""

    def test_invalid_json(self):
        """Test applying invalid JSON diff."""
        old = "Hello World"
        diff = "invalid json"
        with pytest.raises(json.JSONDecodeError):
            apply_diff(old, diff)

    def test_roundtrip(self):
        """Test that compute_diff and apply_diff are inverses."""
        original = "The quick brown fox jumps over the lazy dog"
        modified = "A fast brown fox leaps over a sleeping cat"

        # Compute diff
        diff = compute_diff(original, modified)

        # Apply diff
        reconstructed = apply_diff(original, diff)

        # Should get back the modified text
        assert reconstructed == modified

    def test_large_text(self):
        """Test diff with large text."""
        old = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. " * 100
        new = (
            "Lorem ipsum dolor sit amet, consectetur adipiscing elit. " * 100
            + "Modified"
        )
        diff = compute_diff(old, new)

        # Verify diff is valid JSON
        diff_data = json.loads(diff)
        assert "ops" in diff_data
        assert diff_data["old_len"] == len(old)

        # Verify reconstruction works
        reconstructed = apply_diff(old, diff)
        assert reconstructed == new
