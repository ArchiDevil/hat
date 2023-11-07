from xml.etree import ElementTree


# this is 1.2 version parser as SmartCAT supports only this version
def extract_xliff_content(content: str) -> list[tuple[str, str]]:
    root = ElementTree.fromstring(content)

    version = root.attrib.get("version")
    if not version or version != "1.2":
        raise RuntimeError("Error: XLIFF version is not supported")

    # TODO: support XLIFF namespace

    segments: list[tuple[str, str]] = []
    for unit in root.iter("trans-unit"):
        src_segment = unit.find("source")
        tgt_segment = unit.find("target")

        if not src_segment or not src_segment.text:
            print("Error: <unit> does not have <source>", unit.text)
            continue

        if not tgt_segment or not tgt_segment.text:
            print("Error: <unit> does not have <target>", unit.text)
            continue

        segments.append((src_segment.text, tgt_segment.text))

    return segments
