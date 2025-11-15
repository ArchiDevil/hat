from nltk.stem.snowball import SnowballStemmer
from nltk.tokenize import word_tokenize

stemmer = SnowballStemmer("english")


def stem_sentence(sentence: str) -> list[str]:
    words = word_tokenize(
        sentence.replace("\u2018", "'").replace("\u2019", "'").replace("\u201b", "'")
    )
    # should we use stopwords?
    # words = [word for word in words if word not in stopwords.words("english")]
    words = [stemmer.stem(word) for word in words]
    return words


def postprocess_stemmed_segment(stemmed_words: list[str]) -> list[str]:
    # remove 's and similar tokenized suffixes, produced by NLTKWordTokenizer
    return [word for word in stemmed_words if not word.startswith("'")]
