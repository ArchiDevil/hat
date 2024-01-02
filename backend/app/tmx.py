from lxml import etree


def __parse_seg(seg: etree._Element) -> str:
    return "".join(seg.itertext())


def extract_tmx_content(
    content: bytes, orig_lang="en", tran_lang="ru"
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
        orig_search_string = f".//tuv[@lang='{orig_lang}' or @xml:lang='{orig_lang}']"
        tran_search_string = f".//tuv[@lang='{tran_lang}' or @xml:lang='{tran_lang}']"
        orig_tuv: etree._Element | None = tu.xpath(orig_search_string, namespaces=nsmap)
        tran_tuv: etree._Element | None = tu.xpath(tran_search_string, namespaces=nsmap)

        if orig_tuv is None:
            print("Error: original <tu> does not have specified language", tu.text)
            continue

        if tran_tuv is None:
            print("Error: translation <tu> does not have specified language", tu.text)
            continue

        orig_tuv = orig_tuv[0]
        tran_tuv = tran_tuv[0]

        original, translation = "", ""
        # find <seg> in orig_tuv
        seg = orig_tuv.find("seg")
        if seg is None:
            raise RuntimeError(
                f"Malformed XML: original <tuv> does not have <seg>, {tu.text}"
            )

        original = __parse_seg(seg)

        seg = tran_tuv.find("seg")
        if seg is None:
            raise RuntimeError(
                f"Malformed XML: translation <tuv> does not have <seg>, {tu.text}"
            )

        translation = __parse_seg(seg)
        segments.append((original, translation))

    return segments
