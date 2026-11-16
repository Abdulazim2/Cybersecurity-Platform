import pytest

import app.services.data_ingestion_service as ingestion


@pytest.fixture
def small_record_limit(monkeypatch):
    monkeypatch.setattr(ingestion, "MAX_RECORDS", 2)


def test_csv_accepts_records_at_limit(small_record_limit):
    content = (
        "timestamp,source,level,message\n"
        "2026-01-01T00:00:00Z,host1,INFO,test1\n"
        "2026-01-01T00:01:00Z,host2,WARNING,test2\n"
    ).encode("utf-8")

    result = ingestion.process_uploaded_file(
        "test.csv", content, "system_logs"
    )

    assert result["records_count"] == 2


def test_csv_rejects_records_over_limit(small_record_limit):
    content = (
        "timestamp,source,level,message\n"
        "2026-01-01T00:00:00Z,host1,INFO,test1\n"
        "2026-01-01T00:01:00Z,host2,WARNING,test2\n"
        "2026-01-01T00:02:00Z,host3,ERROR,test3\n"
    ).encode("utf-8")

    with pytest.raises(ValueError, match="record limit"):
        ingestion.process_uploaded_file(
            "test.csv", content, "system_logs"
        )


def test_json_accepts_records_at_limit(small_record_limit):
    content = b"""
    [
        {
            "timestamp": "2026-01-01T00:00:00Z",
            "source": "host1",
            "level": "INFO",
            "message": "test1"
        },
        {
            "timestamp": "2026-01-01T00:01:00Z",
            "source": "host2",
            "level": "WARNING",
            "message": "test2"
        }
    ]
    """

    result = ingestion.process_uploaded_file(
        "test.json", content, "system_logs"
    )

    assert result["records_count"] == 2


def test_json_rejects_records_over_limit(small_record_limit):
    content = b"""
    [
        {
            "timestamp": "2026-01-01T00:00:00Z",
            "source": "host1",
            "level": "INFO",
            "message": "test1"
        },
        {
            "timestamp": "2026-01-01T00:01:00Z",
            "source": "host2",
            "level": "WARNING",
            "message": "test2"
        },
        {
            "timestamp": "2026-01-01T00:02:00Z",
            "source": "host3",
            "level": "ERROR",
            "message": "test3"
        }
    ]
    """

    with pytest.raises(ValueError, match="record limit"):
        ingestion.process_uploaded_file(
            "test.json", content, "system_logs"
        )