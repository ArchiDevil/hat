from lxml import etree


def extract_tmx_content(
    content: bytes, orig_lang="en", trans_lang="ru"
) -> list[tuple[str, str]]:
    root: etree._Element = etree.fromstring(
        content, parser=etree.XMLParser(recover=True)
    )

    version = root.attrib["version"]
    if not version or version != "1.4":
        raise RuntimeError("Unsupported TMX version")

    nsmap = {"xml": "http://www.w3.org/XML/1998/namespace"}

    segments: list[tuple[str, str]] = []
    for tu in root.iter("tu"):
        orig_tuv = tu.find(f".//tuv[@xml:lang='{orig_lang}']", namespaces=nsmap)
        trans_tuv = tu.find(f".//tuv[@xml:lang='{trans_lang}']", namespaces=nsmap)
        if orig_tuv is None:
            print("Error: original <tu> does not have specified language", tu.text)
            continue

        if trans_tuv is None:
            print("Error: translation <tu> does not have specified language", tu.text)
            continue

        original, translation = "", ""
        # find <seg> in orig_tuv
        for seg in orig_tuv.iter("seg"):
            text_iter = list(seg.itertext())
            original = "".join(text_iter)

        # find <seg> in trans_tuv
        for seg in trans_tuv.iter("seg"):
            text_iter = list(seg.itertext())
            translation = "".join(text_iter)

        segments.append((original, translation))

    return segments
