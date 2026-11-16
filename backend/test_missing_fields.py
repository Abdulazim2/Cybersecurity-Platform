import pytest

from app.services.data_ingestion_service import process_uploaded_file


def test_csv_missing_required_field():
    csv_content = (
        b"timestamp,source,level,message\n"
        b"2026-11-16T10:00:00,server,INFO\n"
    )

    with pytest.raises(ValueError):
        process_uploaded_file(
            "missing_required.csv",
            csv_content,
            "system_logs"
        )


def test_csv_missing_optional_field():
    csv_content = (
        b"timestamp,source_ip,destination_ip,protocol,packet_count,source_port\n"
        b"2026-11-16T10:00:00,192.168.1.1,192.168.1.2,TCP,10\n"
    )

    result = process_uploaded_file(
        "missing_optional.csv",
        csv_content,
        "traffic_logs"
    )

    assert result["records_count"] == 1
    assert result["records"][0]["source_port"] is None


def test_json_records_with_different_optional_fields():
    json_content = b"""
    [
        {
            "timestamp": "2026-11-16T10:00:00",
            "source_ip": "192.168.1.1",
            "destination_ip": "192.168.1.2",
            "protocol": "TCP",
            "packet_count": 10
        },
        {
            "timestamp": "2026-11-16T10:01:00",
            "source_ip": "192.168.1.3",
            "destination_ip": "192.168.1.4",
            "protocol": "UDP",
            "packet_count": 20,
            "bytes_transferred": 500
        }
    ]
    """

    result = process_uploaded_file(
        "different_fields.json",
        json_content,
        "traffic_logs"
    )

    assert result["records_count"] == 2
    assert "bytes_transferred" in result["columns"]
    assert result["records"][0]["bytes_transferred"] is None
    assert result["records"][1]["bytes_transferred"] == 500