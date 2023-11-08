from xml.etree import ElementTree


class XliffSegment:
    def __init__(self, source: str, target: str) -> None:
        self.__source = source
        self.__target = target

    @property
    def original(self) -> str:
        return self.__source

    @property
    def translation(self) -> str:
        return self.__target

    @translation.setter
    def translation(self, value: str) -> None:
        # TODO put data into XML document by ID
        self.__target = value

    def __str__(self) -> str:
        return f"XliffSegment({self.__source}, {self.__target})"

    def __repr__(self) -> str:
        return self.__str__()


class XliffData:
    def __init__(self, segments: list[XliffSegment]) -> None:
        self.__segments = segments

    def segments(self) -> list[XliffSegment]:
        return self.__segments


# this is 1.2 version parser as SmartCAT supports only this version
def extract_xliff_content(content: str) -> XliffData:
    root = ElementTree.fromstring(content)

    version = root.attrib.get("version")
    if not version or version != "1.2":
        raise RuntimeError("Error: XLIFF version is not supported")

    # TODO: support XLIFF namespace urn:oasis:names:tc:xliff:document:1.2
    # TODO: support XLIFFs without namespaces
    # TODO: support accepted attribute

    segments: list[XliffSegment] = []
    for unit in root.iter("{urn:oasis:names:tc:xliff:document:1.2}trans-unit"):
        src_segment = unit.find("{urn:oasis:names:tc:xliff:document:1.2}source")
        tgt_segment = unit.find("{urn:oasis:names:tc:xliff:document:1.2}target")

        if src_segment is None or not src_segment.text:
            print("Error: <unit> does not have <source>", unit.text)
            continue

        if tgt_segment is None or not tgt_segment.text:
            print("Error: <unit> does not have <target>", unit.text)
            continue

        # TODO collect XML data instead of raw values
        segments.append(XliffSegment(src_segment.text, tgt_segment.text))

    return XliffData(segments)
