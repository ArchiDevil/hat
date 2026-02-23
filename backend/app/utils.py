def encode_to_latin_1(original: str):
    output = ""
    for c in original:
        output += c if (c.isascii() and c.isalnum() or c in "'().[] -") else "_"
    return output
