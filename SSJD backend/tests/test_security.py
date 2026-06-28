"""Tests for password hashing — must handle arbitrary-length inputs."""

from app.core.security import hash_password, verify_password


def test_hash_and_verify_roundtrip():
    h = hash_password("s3cret-pw")
    assert h != "s3cret-pw"
    assert verify_password("s3cret-pw", h) is True
    assert verify_password("wrong", h) is False


def test_handles_passwords_longer_than_bcrypt_72_byte_limit():
    # bcrypt truncates at 72 bytes; the SHA256 pre-hash must make long pws work.
    long_pw = "a" * 200
    h = hash_password(long_pw)
    assert verify_password(long_pw, h) is True
    # A different long password must not collide.
    assert verify_password("b" * 200, h) is False
