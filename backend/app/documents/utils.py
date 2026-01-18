"""Utility functions for document operations."""

import difflib
import json
from typing import Iterable


def compute_diff(old_text: str, new_text: str) -> str:
    """
    Compute a compact JSON diff between two text strings using SequenceMatcher opcodes.

    The diff format stores only the changes, not full context, making it more
    storage-efficient than the unified diff format.

    Args:
        old_text: The original text
        new_text: The new text

    Returns:
        A JSON string containing opcodes that represent the changes
    """

    matcher = difflib.SequenceMatcher(None, old_text, new_text)
    opcodes = matcher.get_opcodes()

    # Convert opcodes to compact JSON format
    ops = []
    for tag, i1, i2, j1, j2 in opcodes:
        if tag == "equal":
            ops.append([tag, i1, i2])
        elif tag == "replace":
            # Replace old_text[i1:i2] with new_text[j1:j2]
            new_segment = new_text[j1:j2]
            ops.append([tag, i1, i2, new_segment])
        elif tag == "delete":
            # Delete old_text[i1:i2]
            ops.append([tag, i1, i2])
        elif tag == "insert":
            # Insert new_text[j1:j2] at position i1
            new_segment = new_text[j1:j2]
            ops.append([tag, i1, i2, new_segment])

    diff_data = {"ops": ops, "old_len": len(old_text)}

    return json.dumps(diff_data)


def apply_diff(old_text: str, diff_json: str) -> str:
    """
    Apply a compact JSON diff to reconstruct new text from old text.

    Args:
        old_text: The original text
        diff_json: JSON string containing opcodes from compute_diff()

    Returns:
        The reconstructed new text
    """
    if not diff_json:
        return old_text

    diff = json.loads(diff_json)
    result = []

    for op in diff["ops"]:
        op_type = op[0]

        if op_type == "equal":
            # Keep unchanged text
            i1, i2 = op[1], op[2]
            result.append(old_text[i1:i2])
        elif op_type == "replace":
            # Replace old text with new
            new_segment = op[3]
            result.append(new_segment)
        elif op_type == "delete":
            # Delete old text (skip)
            pass
        elif op_type == "insert":
            # Insert new text
            new_segment = op[3]
            result.append(new_segment)

    return "".join(result)


def reconstruct_from_diffs(diff_jsons: Iterable[str]) -> str:
    cumulative_str = ""

    for diff in diff_jsons:
        cumulative_str = apply_diff(cumulative_str, diff)

    return cumulative_str
