
from app.core.security import (
    generate_sensor_token,
    hash_sensor_token,
    verify_sensor_token
)


def test_generate_sensor_token():
    token = generate_sensor_token()

    assert isinstance(token, str)
    assert len(token) > 30


def test_sensor_tokens_are_unique():
    token1 = generate_sensor_token()
    token2 = generate_sensor_token()

    assert token1 != token2


def test_hash_sensor_token():
    token = generate_sensor_token()
    token_hash = hash_sensor_token(token)

    assert token_hash != token
    assert len(token_hash) == 64


def test_verify_correct_sensor_token():
    token = generate_sensor_token()
    token_hash = hash_sensor_token(token)

    assert verify_sensor_token(token, token_hash) is True


def test_reject_wrong_sensor_token():
    token = generate_sensor_token()
    wrong_token = generate_sensor_token()

    token_hash = hash_sensor_token(token)

    assert verify_sensor_token(wrong_token, token_hash) is False


def test_reject_empty_sensor_token():
    token = generate_sensor_token()
    token_hash = hash_sensor_token(token)

    assert verify_sensor_token("", token_hash) is False


def test_reject_empty_stored_hash():
    token = generate_sensor_token()

    assert verify_sensor_token(token, "") is False
