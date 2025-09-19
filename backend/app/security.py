import base64
import hashlib
import secrets

SALT_SIZE = 16
ROUNDS = 29000


def _b64_decode(data: str) -> bytes:
    current_len = len(data)
    to_pad = 4 - (current_len % 4)
    padded = data + ("=" * to_pad)
    padded = padded.replace(".", "+")
    return base64.b64decode(padded)


def _b64_encode(data: bytes) -> str:
    decoded = base64.b64encode(data).decode("ascii")
    decoded = decoded.rstrip("=")
    return decoded.replace("+", ".")


def verify_password(password: str, hash_: str) -> bool:
    algo, rounds, salt_base64, pass_base64 = hash_.split("$")[1:]
    if algo != "pbkdf2-sha256":  # we do not support other than this
        return False

    rounds = int(rounds)
    salt = _b64_decode(salt_base64)
    pass_ = _b64_decode(pass_base64)

    expected = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, rounds)
    return secrets.compare_digest(expected, pass_)


def hash_password(password: str) -> str:
    algo = "pbkdf2-sha256"
    rounds = ROUNDS
    salt = secrets.token_bytes(SALT_SIZE)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, rounds)
    return f"${algo}${rounds}${_b64_encode(salt)}${_b64_encode(dk)}"
