class TranslationError(Exception):
    """
    An error raised when Machine Translator API returns an error.
    """


Original = str
Translation = str
GlossaryPair = tuple[Original, Translation]
GlossaryPairs = list[GlossaryPair]
LineWithGlossaries = tuple[str, GlossaryPairs]
