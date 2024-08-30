from passlib.context import CryptContext

password_hasher = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def verify_password(password: str, hash_: str) -> bool:
    return password_hasher.verify(password, hash_)


def hash_password(password: str) -> str:
    return password_hasher.hash(password)
