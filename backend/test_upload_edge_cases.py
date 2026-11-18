
import pytest

from app.services.data_ingestion_service import (
    MAX_FILE_SIZE,
    normalize_filename,
    process_uploaded_file,
)


@pytest.mark.parametrize(
    "filename, content, dataset_type, expected_error",
    [
        (
            "empty.csv",
            b"",
            "traffic_logs",
            "Uploaded file is empty",
        ),
        (
            "unsupported.txt",
            b"some test content",
            "traffic_logs",
            "Only CSV and JSON files are supported",
        ),
        (
            "large.csv",
            b"A" * (MAX_FILE_SIZE + 1),
            "traffic_logs",
            "File size exceeds the 10 MB limit",
        ),
        (
            "valid.csv",
            b"test content",
            "unknown_dataset",
            "Unsupported dataset type",
        ),
    ],
    ids=[
        "empty-file",
        "unsupported-extension",
        "file-exceeds-10mb",
        "unsupported-dataset-type",
    ],
)
def test_upload_edge_cases(
    filename,
    content,
    dataset_type,
    expected_error,
):
    with pytest.raises(ValueError, match=expected_error):
        process_uploaded_file(
            filename=filename,
            file_content=content,
            dataset_type=dataset_type,
        )
@pytest.mark.parametrize(
    "filename, expected",
    [
        ("data.csv", "data.csv"),
        ("C:\\Users\\Admin\\data.csv", "data.csv"),
        ("/home/user/data.json", "data.json"),
        ("folder\\nested\\traffic.csv", "traffic.csv"),
        ("  traffic.csv  ", "traffic.csv"),
    ],
    ids=[
        "normal-filename",
        "windows-path",
        "linux-path",
        "nested-path",
        "trim-whitespace",
    ],
)
def test_normalize_valid_filename(filename, expected):
    assert normalize_filename(filename) == expected


@pytest.mark.parametrize(
    "filename, expected_error",
    [
        ("", "Filename cannot be empty"),
        ("   ", "Filename cannot be empty"),
        (".", "Invalid filename"),
        ("..", "Invalid filename"),
        ("...", "Invalid filename"),
        ("bad\nname.csv", "control characters"),
        ("a" * 256 + ".csv", "255 characters"),
        (None, "Invalid filename"),
    ],
    ids=[
        "empty",
        "whitespace-only",
        "dot",
        "double-dot",
        "dots-only",
        "newline",
        "too-long",
        "not-a-string",
    ],
)
def test_normalize_invalid_filename(filename, expected_error):
    with pytest.raises(ValueError, match=expected_error):
        normalize_filename(filename)


def test_process_uploaded_file_stores_normalized_filename():
    content = (
        b"timestamp,source_ip,destination_ip,protocol,packet_count\n"
        b"2026-11-05T10:00:00,192.168.1.1,192.168.1.2,TCP,10"
    )

    result = process_uploaded_file(
        filename="C:\\Users\\Admin\\traffic.csv",
        file_content=content,
        dataset_type="traffic_logs",
    )

    assert result["filename"] == "traffic.csv"