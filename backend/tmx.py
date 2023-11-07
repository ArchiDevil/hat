from xml.etree import ElementTree


def extract_tmx_content(
    content: str, orig_lang="en", trans_lang="ru"
) -> list[tuple[str, str]]:
    # this method reads and extract pairs from a TMX file content
    # returns a list of tuples
    root = ElementTree.fromstring(content)
    pairs: list[tuple[str, str]] = []
    for tu in root.iter("tu"):
        orig_tuv = tu.find(f"./tuv[@lang='{orig_lang}']")
        trans_tuv = tu.find(f"./tuv[@lang='{trans_lang}']")
        if orig_tuv is None:
            print("Error: original <tu> does not have specified language", tu.text)
            continue

        if trans_tuv is None:
            print("Error: translation <tu> does not have specified language", tu.text)
            continue

        original, translation = "", ""
        # find <seg> in orig_tuv
        for seg in orig_tuv.iter("seg"):
            if seg.text is not None:
                original += seg.text

        # find <seg> in trans_tuv
        for seg in trans_tuv.iter("seg"):
            if seg.text is not None:
                translation += seg.text

        pairs.append((original, translation))

    return pairs
