
import pytest

from app.services.data_ingestion_service import process_uploaded_file


VALID_DATASETS = [
    pytest.param(
        "test_traffic.csv",
        "traffic_logs",
        2,
        id="traffic-csv",
    ),
    pytest.param(
        "test_traffic.json",
        "traffic_logs",
        2,
        id="traffic-json",
    ),
    pytest.param(
        "test_system.csv",
        "system_logs",
        2,
        id="system-csv",
    ),
]
@pytest.mark.parametrize(
    "content",
    [
        b"""[
            {
                "timestamp": "2026-11-05T10:00:00",
                "source": "Firewall",
                "level": "INFO",
                "message": "Connection accepted"
            }
        ]""",
        b"""{
            "timestamp": "2026-11-05T10:00:00",
            "source": "Firewall",
            "level": "INFO",
            "message": "Connection accepted"
        }""",
    ],
    ids=["system-json-list", "system-json-object"],
)
def test_system_logs_json(content):
    result = process_uploaded_file(
        "system.json",
        content,
        "system_logs",
    )

    assert result["dataset_type"] == "system_logs"
    assert result["records_count"] == 1
    assert result["records"][0]["source"] == "Firewall"
    assert result["records"][0]["level"] == "INFO"

@pytest.mark.parametrize(
    "filename, dataset_type, expected_records",
    VALID_DATASETS,
)
def test_existing_datasets(filename, dataset_type, expected_records):
    with open(filename, "rb") as file:
        content = file.read()

    result = process_uploaded_file(
        filename,
        content,
        dataset_type,
    )

    assert result["dataset_type"] == dataset_type
    assert result["records_count"] == expected_records
    assert len(result["records"]) == expected_records
    assert len(result["columns"]) > 0


@pytest.mark.parametrize(
    "dataset_type, filename, content",
    [
        (
            "iot_logs",
            "iot.csv",
            b"timestamp,device_id,device_type,source_ip,event_type,status,temperature\n"
            b"2026-11-05T10:00:00,device_001,Sensor,192.168.1.30,Temperature_Read,Active,25.5",
        ),
        (
            "iot_logs",
            "iot.json",
            b'[{"timestamp":"2026-11-05T10:00:00","device_id":"device_002",'
            b'"device_type":"Camera","source_ip":"192.168.1.31",'
            b'"event_type":"Motion_Detected","status":"Active","temperature":28.5}]',
        ),
        (
            "authorization_logs",
            "authorization.csv",
            b"timestamp,username,source_ip,action,resource,status,authentication_method\n"
            b"2026-11-05T11:00:00,analyst1,192.168.1.40,LOGIN,Dashboard,SUCCESS,Password",
        ),
        (
            "authorization_logs",
            "authorization.json",
            b'[{"timestamp":"2026-11-05T11:30:00","username":"analyst2",'
            b'"source_ip":"192.168.1.41","action":"ACCESS",'
            b'"resource":"Factory_Reports","status":"SUCCESS",'
            b'"authentication_method":"MFA"}]',
        ),
    ],
    ids=[
        "iot-csv",
        "iot-json",
        "authorization-csv",
        "authorization-json",
    ],
)
def test_iot_and_authorization_datasets(dataset_type, filename, content):
    result = process_uploaded_file(
        filename,
        content,
        dataset_type,
    )

    assert result["dataset_type"] == dataset_type
    assert result["records_count"] == 1
    assert len(result["records"]) == 1

    record = result["records"][0]

    assert record["timestamp"].startswith("2026-11-05T")

    if dataset_type == "iot_logs":
        assert record["device_id"]
        assert isinstance(record["temperature"], float)
    else:
        assert record["username"]
        assert record["authentication_method"]
