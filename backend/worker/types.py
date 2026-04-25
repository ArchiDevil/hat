from enum import Enum
from typing import Literal, overload

from app.formats.txt import TxtSegment
from app.formats.xliff import XliffSegment

type FormatSegment = XliffSegment | TxtSegment


class RecordSource(Enum):
    glossary = "glossary"
    machine_translation = "mt"
    translation_memory = "tm"
    full_match = "fm"  # for digits


class WorkerSegment:
    @overload
    def __init__(
        self, *, type_: Literal["xliff"], original_segment: XliffSegment
    ) -> None: ...

    @overload
    def __init__(
        self, *, type_: Literal["txt"], original_segment: TxtSegment
    ) -> None: ...

    def __init__(
        self,
        *,
        type_: Literal["xliff", "txt"],
        original_segment: FormatSegment,
    ) -> None:
        self._segment_src = None
        self._type = type_
        self._approved = False
        self.original_segment = original_segment
        assert (type_ == "xliff" and isinstance(original_segment, XliffSegment)) or (
            type_ == "txt" and isinstance(original_segment, TxtSegment)
        )
        if isinstance(original_segment, XliffSegment):
            self._approved = original_segment.approved

    @property
    def segment_source(self) -> RecordSource | None:
        return self._segment_src

    @segment_source.setter
    def segment_source(self, value: RecordSource | None):
        self._segment_src = value

    @property
    def approved(self):
        return self._approved

    @approved.setter
    def approved(self, value: bool):
        self._approved = value

    @property
    def type_(self):
        return self._type

    @property
    def needs_processing(self) -> bool:
        if isinstance(self.original_segment, XliffSegment):
            return not self.original_segment.approved
        return True
