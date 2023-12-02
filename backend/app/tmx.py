from lxml import etree


def __parse_seg(seg: etree._Element) -> str:
    text_iter = list(seg.itertext())
    return "".join(text_iter)


def extract_tmx_content(
    content: bytes, orig_lang="en", trans_lang="ru"
) -> list[tuple[str, str]]:
    root: etree._Element = etree.fromstring(
        content, parser=etree.XMLParser(recover=True)
    )

    version = root.attrib["version"]
    if not version or version not in ["1.1", "1.4"]:
        raise RuntimeError("Unsupported TMX version")

    nsmap = {
        "xml": "http://www.w3.org/XML/1998/namespace",
    }

    segments: list[tuple[str, str]] = []
    for tu in root.iter("tu"):
        for tuv in tu.iter('tuv'):
            pass

        orig_tuv: etree._Element | None = tu.find(
            ".//tuv[@lang='en'] or .//tuv[@xml:lang='en']", namespaces=nsmap
        )
        trans_tuv: etree._Element | None = tu.find(
            ".//tuv[@lang='ru'] or .//tuv[@xml:lang='ru']", namespaces=nsmap
        )
        if orig_tuv is None:
            print("Error: original <tu> does not have specified language", tu.text)
            continue

        if trans_tuv is None:
            print("Error: translation <tu> does not have specified language", tu.text)
            continue

        original, translation = "", ""
        # find <seg> in orig_tuv
        seg = orig_tuv.find("seg")
        if seg is None:
            raise RuntimeError(
                f"Malformed XML: original <tuv> does not have <seg>, {tu.text}"
            )

        original = __parse_seg(seg)

        seg = trans_tuv.find("seg")
        if seg is None:
            raise RuntimeError(
                f"Malformed XML: translation <tuv> does not have <seg>, {tu.text}"
            )

        translation = __parse_seg(seg)
        segments.append((original, translation))

    return segments
