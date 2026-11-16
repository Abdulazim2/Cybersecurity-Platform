import pytest

from app.services.data_ingestion_service import normalize_records


def make_iot_record():
    return {
        "timestamp": "2026-11-06T10:00:00Z",
        "device_id": "DEV-001",
        "device_type": "Temperature Sensor",
        "source_ip": "192.168.1.10",
        "event_type": "normal_reading",
        "temperature": "25.5",
        "status": "active"
    }


def make_authorization_record():
    return {
        "timestamp": "2026-11-06T10:00:00Z",
        "username": "operator1",
        "source_ip": "192.168.1.20",
        "action": "login",
        "resource": "dashboard",
        "status": "success",
        "authentication_method": "password"
    }


def test_iot_rejects_invalid_ip():
    record = make_iot_record()
    record["source_ip"] = "999.999.999.999"

    with pytest.raises(ValueError, match="Invalid IP address"):
        normalize_records([record], "iot_logs", list(record.keys()))


@pytest.mark.parametrize("temperature", ["-10", "nan"])
def test_iot_rejects_invalid_temperature(temperature):
    record = make_iot_record()
    record["temperature"] = temperature

    with pytest.raises(ValueError, match="temperature"):
        normalize_records([record], "iot_logs", list(record.keys()))


def test_iot_rejects_missing_device_id():
    record = make_iot_record()
    del record["device_id"]

    with pytest.raises(ValueError, match="Missing required columns"):
        normalize_records([record], "iot_logs", list(record.keys()))


def test_authorization_rejects_invalid_ip():
    record = make_authorization_record()
    record["source_ip"] = "invalid-ip"

    with pytest.raises(ValueError, match="Invalid IP address"):
        normalize_records(
            [record],
            "authorization_logs",
            list(record.keys())
        )


def test_authorization_rejects_missing_username():
    record = make_authorization_record()
    del record["username"]

    with pytest.raises(ValueError, match="Missing required columns"):
        normalize_records(
            [record],
            "authorization_logs",
            list(record.keys())
        )

def test_iot_accepts_missing_temperature():
    record = make_iot_record()
    record.pop("temperature")

    result = normalize_records(
        [record], "iot_logs", list(record.keys())
    )

    assert "temperature" in result[0]
    assert result[0]["temperature"] is None


def test_iot_accepts_empty_optional_temperature():
    record = make_iot_record()
    record["temperature"] = ""

    result = normalize_records(
        [record], "iot_logs", list(record.keys())
    )

    assert result[0]["temperature"] is None


def test_iot_rejects_non_numeric_temperature():
    record = make_iot_record()
    record["temperature"] = "hot"

    with pytest.raises(ValueError, match="temperature"):
        normalize_records(
            [record], "iot_logs", list(record.keys())
        )


def test_authorization_rejects_invalid_timestamp():
    record = make_authorization_record()
    record["timestamp"] = "not-a-date"

    with pytest.raises(ValueError, match="Invalid timestamp"):
        normalize_records(
            [record],
            "authorization_logs",
            list(record.keys())
        )


def test_authorization_rejects_empty_username():
    record = make_authorization_record()
    record["username"] = "   "

    with pytest.raises(ValueError, match="cannot be empty"):
        normalize_records(
            [record],
            "authorization_logs",
            list(record.keys())
        )
def test_system_logs_rejects_numeric_level():
    record = {
        "timestamp": "2026-11-06T10:00:00Z",
        "source": "server-1",
        "level": 123,
        "message": "Test message"
    }

    with pytest.raises(ValueError, match="level must be text"):
        normalize_records(
            [record],
            "system_logs",
            list(record.keys())
        )


def test_system_logs_normalizes_text_level():
    record = {
        "timestamp": "2026-11-06T10:00:00Z",
        "source": "server-1",
        "level": "warning",
        "message": "Test message"
    }

    result = normalize_records(
        [record],
        "system_logs",
        list(record.keys())
    )

    assert result[0]["level"] == "WARNING"