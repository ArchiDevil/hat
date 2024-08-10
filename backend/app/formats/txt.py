from io import BytesIO

from nltk import PunktSentenceTokenizer

from .base import BaseSegment


class TxtSegment(BaseSegment):
    def __init__(self, id_: int, source: str, target: str | None, offset: int) -> None:
        super().__init__(id_, source, target)
        self._offset = offset

    @property
    def offset(self) -> int:
        return self._offset


class TxtData:
    def __init__(self, segments: list[TxtSegment], original_content: str):
        self._segments = segments
        self._content = original_content

    @property
    def segments(self):
        return self._segments

    def commit(self):
        new_content = ""
        last_start = 0
        for segment in self._segments:
            new_content += self._content[last_start : segment.offset]
            new_content += segment.translation or segment.original
            last_start = segment.offset + len(segment.original)
        new_content += self._content[last_start:]
        self._content = new_content

    def write(self) -> BytesIO:
        file = BytesIO()
        file.write(self._content.encode())
        file.seek(0)
        return file


def extract_txt_content(content: str) -> TxtData:
    tokenizer = PunktSentenceTokenizer()
    segments: list[TxtSegment] = []
    lines = content.splitlines(keepends=True)
    line_offset = 0
    id_ = 1
    for line in lines:
        padded_offset = len(line) - len(line.lstrip())
        spans = tokenizer.span_tokenize(line.lstrip())
        for b, e in spans:
            segments.append(
                TxtSegment(
                    id_,
                    line[padded_offset + b : padded_offset + e],
                    None,
                    line_offset + padded_offset + b,
                )
            )
            id_ += 1
        line_offset += len(line)
    return TxtData(segments, content)
