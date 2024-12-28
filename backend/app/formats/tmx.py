from datetime import datetime
from io import BytesIO
from typing import NamedTuple

from lxml import etree

from .base import get_seg_text

DEFAULT_NSMAP = {"xml": "http://www.w3.org/XML/1998/namespace"}


class TmxSegment(NamedTuple):
    original: str
    translation: str
    creation_date: datetime | None
    change_date: datetime | None


class TmxData:
    # This class is used to create a new TMX file. It cannot manipulate the
    # existing TMX file.

    def __init__(self, segments: list[TmxSegment]) -> None:
        self.__segments = segments
        self.__root = etree.fromstring(
            b'<?xml version="1.0" encoding="utf-8"?><tmx version="1.4"></tmx>',
            parser=etree.XMLParser(recover=True),
        )

    def write(self) -> BytesIO:
        etree.SubElement(
            self.__root,
            "header",
            attrib={
                "creationtool": "HAT",
                # TODO: should not be this updated when any format changes
                # happen in a tool parser/serializer?
                "creationtoolversion": "1.0",
                "segtype": "sentence",
                "o-tmf": "ATM",
                "adminlang": "en-US",
                "srclang": "en",
                "datatype": "plaintext",
            },
            nsmap={},
        )
        body = etree.SubElement(self.__root, "body", None, None)
        for segment in self.__segments:
            tu = etree.SubElement(body, "tu", None, None)
            origin = etree.SubElement(
                tu,
                "tuv",
                attrib={"{%s}lang" % DEFAULT_NSMAP["xml"]: "en"},
                nsmap=DEFAULT_NSMAP,
            )
            seg = etree.SubElement(origin, "seg", None, None)
            seg.text = segment.original

            target = etree.SubElement(
                tu,
                "tuv",
                attrib={"{%s}lang" % DEFAULT_NSMAP["xml"]: "ru"},
                nsmap=DEFAULT_NSMAP,
            )
            seg = etree.SubElement(target, "seg", None, None)
            seg.text = segment.translation

        output = BytesIO()
        et: etree._ElementTree = etree.ElementTree(self.__root)
        et.write(output, xml_declaration=True, encoding="utf-8")
        output.seek(0)
        return output


def extract_tmx_content(
    content: bytes, orig_lang="en", tran_lang="ru"
) -> list[TmxSegment]:
    root: etree._Element = etree.fromstring(
        content, parser=etree.XMLParser(recover=True)
    )

    version = root.attrib["version"]
    if not version or version not in ["1.1", "1.4"]:
        raise RuntimeError("Unsupported TMX version")

    segments: list[TmxSegment] = []
    for tu in root.iter("tu"):
        creation_date = None
        if "creationdate" in tu.attrib:
            creation_date = datetime.strptime(
                tu.attrib["creationdate"], "%Y%m%dT%H%M%SZ"
            )

        change_date = None
        if "changedate" in tu.attrib:
            change_date = datetime.strptime(tu.attrib["changedate"], "%Y%m%dT%H%M%SZ")

        orig_search_string = f".//tuv[@lang='{orig_lang}' or @xml:lang='{orig_lang}']"
        tran_search_string = f".//tuv[@lang='{tran_lang}' or @xml:lang='{tran_lang}']"
        orig_tuv: etree._Element | None = tu.xpath(
            orig_search_string, namespaces=DEFAULT_NSMAP
        )
        tran_tuv: etree._Element | None = tu.xpath(
            tran_search_string, namespaces=DEFAULT_NSMAP
        )

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

        original = get_seg_text(seg)

        seg = tran_tuv.find("seg")
        if seg is None:
            raise RuntimeError(
                f"Malformed XML: translation <tuv> does not have <seg>, {tu.text}"
            )

        translation = get_seg_text(seg)
        segments.append(
            TmxSegment(
                original=original,
                translation=translation,
                creation_date=creation_date,
                change_date=change_date,
            )
        )

    return segments
