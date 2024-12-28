from lxml import etree


class BaseSegment:
    def __init__(self, id_: int, source: str, target: str | None) -> None:
        self._id = id_
        self._source = source
        self._target = target

    @property
    def id_(self) -> int:
        return self._id

    @property
    def original(self) -> str:
        return self._source

    @property
    def translation(self) -> str | None:
        return self._target

    @translation.setter
    def translation(self, value: str | None):
        self._target = value


def get_seg_text(seg: etree._Element) -> str:
    return "".join(seg.itertext())
