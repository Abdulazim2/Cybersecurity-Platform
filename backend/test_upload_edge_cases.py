
import pytest

from app.services.data_ingestion_service import (
    MAX_FILE_SIZE,
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
