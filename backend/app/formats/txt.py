from nltk import PunktSentenceTokenizer

from .base import BaseSegment


class TxtSegment(BaseSegment):
    def __init__(self, id_: int, source: str, target: str, offset: int) -> None:
        super().__init__(id_, source, target)
        self._offset = offset

    @property
    def offset(self) -> int:
        return self._offset


class TxtData:
    def __init__(self, segments: list[TxtSegment]):
        self._segments = segments

    @property
    def segments(self):
        return self._segments


def extract_txt_content(content: str) -> TxtData:
    tokenizer = PunktSentenceTokenizer()
    segments: list[TxtSegment] = []
    lines = content.splitlines(keepends=True)
    line_offset = 0
    id_ = 1
    for line in lines:
        spans = tokenizer.span_tokenize(line)
        for b, e in spans:
            segments.append(TxtSegment(id_, line[b:e], "", line_offset + b))
            id_ += 1
        line_offset += len(line)
    return TxtData(segments)
