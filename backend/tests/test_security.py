from app.security import hash_password, verify_password


def test_verifies_hash():
    hash = hash_password("qwerty")
    assert verify_password("qwerty", hash)
