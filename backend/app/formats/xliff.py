from enum import Enum
from io import BytesIO
from typing import Optional

from lxml import etree

from .base import BaseSegment


class SegmentState(Enum):
    # Indicates the terminating state.
    FINAL = "final"

    # Indicates only non-textual information needs adaptation.
    NEEDS_ADAPTATION = "needs-adaptation"

    # Indicates both text and non-textual information needs adaptation.
    NEEDS_L10N = "needs-l10n"

    # Indicates only non-textual information needs review.
    NEEDS_REVIEW_ADAPTATION = "needs-review-adaptation"

    # Indicates both text and non-textual information needs review.
    NEEDS_REVIEW_L10N = "needs-review-l10n"

    # Indicates that only the text of the item needs to be reviewed.
    NEEDS_REVIEW_TRANSLATION = "needs-review-translation"

    # Indicates that the item needs to be translated.
    NEEDS_TRANSLATION = "needs-translation"

    # Indicates that the item is new. For example, translation units that were not in a previous version of the document.
    NEW = "new"

    # Indicates that changes are reviewed and approved.
    SIGNED_OFF = "signed-off"

    # Indicates that the item has been translated.
    TRANSLATED = "translated"


class XliffSegment(BaseSegment):
    def __init__(
        self,
        id_: int,
        approved: Optional[bool],
        source: str,
        target: str,
        state: Optional[str],
    ) -> None:
        super().__init__(id_, source, target)
        self._approved = approved if approved else False
        self._dirty = False
        self._state = SegmentState(state) if state else SegmentState.NEW

    @property
    def approved(self) -> bool:
        return self._approved

    @property
    def state(self) -> SegmentState:
        return self._state

    @property
    def dirty(self) -> bool:
        return self._dirty

    @property
    def translation(self) -> str:
        return super().translation

    @translation.setter
    def translation(self, value: str) -> None:
        self._target = value
        self._state = SegmentState.TRANSLATED
        self._dirty = True

    @approved.setter
    def approved(self, value: bool) -> None:
        self._approved = value
        self._dirty = True

    @state.setter
    def state(self, value: SegmentState) -> None:
        self._state = value

    def __str__(self) -> str:
        return f"XliffSegment({self.id_}, {self._approved}, {self.original}, {self.translation})"

    def __repr__(self) -> str:
        return self.__str__()


class XliffData:
    def __init__(self, segments: list[XliffSegment], root: etree._Element) -> None:
        self.__segments = segments
        self.__root = root

    @property
    def segments(self) -> list[XliffSegment]:
        return self.__segments

    @property
    def xliff_file(self):
        return self.__root

    def commit(self) -> None:
        # go over segments and apply changes to translation and accepted attributes
        # if segment is dirty
        for segment in self.__segments:
            if not segment.dirty:
                continue

            trans_unit = self.__root.find(
                f'.//trans-unit[@id="{segment.id_}"]', namespaces=self.__root.nsmap
            )

            # this is actually a critical error and should never happen!
            assert trans_unit is not None, "Unable to find node"
            trans_unit.attrib["approved"] = "yes" if segment.approved else "no"

            target_node = trans_unit.find(".//target", namespaces=self.__root.nsmap)
            assert target_node is not None, "Unable to find target node"

            for child in target_node.getchildren():
                target_node.remove(child)

            target_node.text = segment.translation
            target_node.attrib["state"] = segment.state.value

    def write(self) -> BytesIO:
        output = BytesIO()
        et: etree._ElementTree = etree.ElementTree(self.__root)
        et.write(output, pretty_print=True, xml_declaration=True, encoding="utf-8")
        return output


# this is 1.2 version parser as SmartCAT supports only this version
def extract_xliff_content(content: bytes) -> XliffData:
    root: etree._Element = etree.fromstring(
        content, parser=etree.XMLParser(recover=True)
    )

    version = root.attrib.get("version")
    if not version or version != "1.2":
        raise RuntimeError("Error: XLIFF version is not supported")

    # TODO: P3 support multi-file XLIFFs

    # The default namespace for XLIFF is a urn:oasis:names:tc:xliff:document:1.2
    # but it can be omitted in the document with lxml

    segments: list[XliffSegment] = []
    for unit in root.iter("{*}trans-unit"):
        segment_id = unit.attrib.get("id")
        approved = unit.attrib.get("approved") == "yes"
        src_segment = unit.find("source", namespaces=root.nsmap)
        tgt_segment = unit.find("target", namespaces=root.nsmap)

        if not segment_id:
            print("Error: <unit> does not have id attribute", unit.text)
            continue

        segment_id = int(segment_id)

        if src_segment is None:
            print("Error: <unit> does not have <source>", unit.text)
            continue

        if tgt_segment is None:
            print("Error: <unit> does not have <target>", unit.text)
            continue

        segments.append(
            XliffSegment(
                segment_id,
                approved,
                "".join(src_segment.itertext()),
                "".join(tgt_segment.itertext()),
                tgt_segment.attrib.get("state"),
            )
        )

    return XliffData(segments, root)
