from passlib.context import CryptContext

password_hasher = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
