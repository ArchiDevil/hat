from typing import Optional
from lxml import etree


class XliffSegment:
    def __init__(
        self, id_: int, approved: Optional[bool], source: str, target: str
    ) -> None:
        self.__id = id_
        self.__approved = approved if approved else False
        self.__source = source
        self.__target = target
        self.__dirty = False

    @property
    def id_(self) -> int:
        return self.__id

    @property
    def approved(self) -> bool:
        return self.__approved

    @property
    def original(self) -> str:
        return self.__source

    @property
    def translation(self) -> str:
        return self.__target

    @property
    def dirty(self) -> bool:
        return self.__dirty

    @translation.setter
    def translation(self, value: str) -> None:
        self.__target = value
        self.__dirty = True

    @approved.setter
    def approved(self, value: bool) -> None:
        self.__approved = value
        self.__dirty = True

    def __str__(self) -> str:
        return f"XliffSegment({self.__id}, {self.__approved}, {self.__source}, {self.__target})"

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

            node = self.__root.find(f'id="{segment.id_}"', namespaces=self.__root.nsmap)

            # this is actually a critical error and should never happen!
            assert node, "Unable to find node"
            node.attrib["approved"] = "yes" if segment.approved else "no"

            target_node = node.find("target")
            assert target_node, "Unable to find target node"
            target_node.text = segment.translation

    def write(self) -> None:
        # TODO: temporary solution, should be replaced with something more robust
        et: etree._ElementTree = etree.ElementTree(self.__root)
        et.write(
            "output.xliff", pretty_print=True, xml_declaration=True, encoding="utf-8"
        )


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
        src_segment = unit.find("{*}source")
        tgt_segment = unit.find("{*}target")

        if not segment_id:
            print("Error: <unit> does not have id attribute", unit.text)
            continue

        segment_id = int(segment_id)

        if src_segment is None or not src_segment.text:
            print("Error: <unit> does not have <source>", unit.text)
            continue

        if tgt_segment is None or not tgt_segment.text:
            print("Error: <unit> does not have <target>", unit.text)
            continue

        segments.append(
            XliffSegment(segment_id, approved, src_segment.text, tgt_segment.text)
        )

    return XliffData(segments, root)
