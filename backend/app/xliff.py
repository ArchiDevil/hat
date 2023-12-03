from typing import Optional
from io import BytesIO
from lxml import etree


class XliffSegment:
    def __init__(
        self,
        id_: int,
        approved: Optional[bool],
        source: str,
        target: str,
        state: Optional[str],
    ) -> None:
        self.__id = id_
        self.__approved = approved if approved else False
        self.__source = source
        self.__target = target
        self.__dirty = False
        self.__state = state

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
    def state(self) -> Optional[str]:
        return self.__state

    @property
    def dirty(self) -> bool:
        return self.__dirty

    @translation.setter
    def translation(self, value: str) -> None:
        self.__target = value
        self.__state = "translated"
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

            trans_unit = self.__root.find(
                f'.//trans-unit[@id="{segment.id_}"]', namespaces=self.__root.nsmap
            )

            # this is actually a critical error and should never happen!
            assert trans_unit is not None, "Unable to find node"
            trans_unit.attrib["approved"] = "yes" if segment.approved else "no"

            target_node = trans_unit.find(".//target", namespaces=self.__root.nsmap)
            assert target_node is not None, "Unable to find target node"

            target_node.text = segment.translation
            target_node.attrib["state"] = segment.state

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
                src_segment.text if src_segment.text else "",
                tgt_segment.text if tgt_segment.text else "",
                tgt_segment.attrib.get("state"),
            )
        )

    return XliffData(segments, root)
