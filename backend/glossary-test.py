from pprint import pprint

from nltk.stem.snowball import SnowballStemmer
from nltk.tokenize import word_tokenize

from sqlalchemy import select, or_
from sqlalchemy.orm import Session

from app.db import get_db
from app.glossary.models import GlossaryRecord

stemmer = SnowballStemmer("english")


def stem_sentence(sentence: str) -> list[str]:
    words = word_tokenize(sentence)
    # should we use stopwords?
    # words = [word for word in words if word not in stopwords.words("english")]
    words = [stemmer.stem(word) for word in words]
    return words


def get_glossary_for_segment(segment: str, session: Session) -> list[tuple[str, str]]:
    words = stem_sentence(segment)
    clauses = [GlossaryRecord.source.ilike(f"%{word}%") for word in words]
    records = session.execute(select(GlossaryRecord).where(or_(*clauses))).scalars()
    found_pairs = [(record.source, record.target) for record in records]
    output: list[tuple[str, str]] = []
    for pair in found_pairs:
        glossary_words = stem_sentence(pair[0])
        found_words = [word for word in glossary_words if word in words]
        if len(found_words) != len(glossary_words):
            continue
        output.append(pair)
    return output


def main():
    session = next(get_db())
    # segment = "This appendix provides an overview of the multiverse, the overarching reality that encompasses D&D’s countless worlds and adventures."
    # segment = "These realms are explored in greater detail in the Dungeon Master's Guide, along with other planes like the Far Realm, Negative Plane, and Positive Plane."
    # segment = "Most D&D adventures take place on the Material Plane, which holds the worlds of settings like Dragonlance, Eberron, the Forgotten Realms, and Greyhawk."
    segment = "Elemental forces and the building blocks of reality originate from these Inner Planes:"
    glossary_records = get_glossary_for_segment(segment, session)
    pprint(glossary_records)
    pprint(f"Count: {len(glossary_records)}")


if __name__ == "__main__":
    main()
