from nltk.stem.snowball import SnowballStemmer
from nltk.tokenize import word_tokenize

stemmer = SnowballStemmer("english")


def stem_sentence(sentence: str) -> list[str]:
    words = word_tokenize(sentence)
    # should we use stopwords?
    # words = [word for word in words if word not in stopwords.words("english")]
    words = [stemmer.stem(word) for word in words]
    return words
