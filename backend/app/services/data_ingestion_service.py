
import csv
import json
import io
import ipaddress
import math
from pathlib import Path
from datetime import datetime


MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

# Temporary limit until the ML team confirms the dataset requirements
MAX_RECORDS = 50_000

ALLOWED_DATASET_TYPES = {
    "system_logs",
    "traffic_logs",
    "iot_logs",
    "authorization_logs"
}

def normalize_filename(filename: str) -> str:
    """
    Normalize an uploaded filename without trusting client-supplied paths.
    Supports both Windows and POSIX path separators.
    """

    if not isinstance(filename, str):
        raise ValueError("Invalid filename")

    if not filename or not filename.strip():
        raise ValueError("Filename cannot be empty")

    if any(ord(char) < 32 or ord(char) == 127 for char in filename):
        raise ValueError("Filename contains invalid control characters")

    normalized = filename.replace("\\", "/").split("/")[-1].strip()

    if not normalized or normalized in {".", ".."}:
        raise ValueError("Invalid filename")

    if not normalized.strip("."):
        raise ValueError("Invalid filename")

    if len(normalized) > 255:
        raise ValueError("Filename cannot exceed 255 characters")

    return normalized
# Initial schemas based on the available test files.
# These schemas should be reviewed with the ML team.
DATASET_SCHEMAS = {
    "system_logs": {
        "required": [
            "timestamp",
            "source",
            "level",
            "message"
        ],
        "optional": []
    },

    "traffic_logs": {
        "required": [
            "timestamp",
            "source_ip",
            "destination_ip",
            "protocol",
            "packet_count"
        ],
        "optional": [
            "source_port",
            "destination_port",
            "bytes_transferred",
            "duration"
        ]
    },

    "iot_logs": {
        "required": [
            "timestamp",
            "device_id",
            "device_type",
            "source_ip",
            "event_type",
            "status"
        ],
        "optional": [
            "temperature"
        ]
    },

    "authorization_logs": {
        "required": [
            "timestamp",
            "username",
            "source_ip",
            "action",
            "resource",
            "status",
            "authentication_method"
        ],
        "optional": []
    }
}


def normalize_timestamp(value, record_number):
    """Validate and normalize an ISO date or datetime."""

    if not isinstance(value, str) or not value.strip():
        raise ValueError(
            f"Record {record_number}: Invalid timestamp"
        )

    try:
        timestamp = datetime.fromisoformat(
            value.strip().replace("Z", "+00:00")
        )
        return timestamp.isoformat()

    except ValueError:
        raise ValueError(
            f"Record {record_number}: Invalid timestamp format"
        )


def normalize_integer(value, field_name, record_number):
    """Convert a value to a non-negative integer."""

    if isinstance(value, bool):
        raise ValueError(
            f"Record {record_number}: {field_name} must be an integer"
        )

    try:
        if isinstance(value, float) and not value.is_integer():
            raise ValueError

        if isinstance(value, str):
            value = value.strip()

        number = int(value)

        if number < 0:
            raise ValueError

        return number

    except (ValueError, TypeError):
        raise ValueError(
            f"Record {record_number}: {field_name} must be a non-negative integer"
        )


def normalize_float(value, field_name, record_number):
    """Convert a value to a finite, non-negative float."""

    if isinstance(value, bool):
        raise ValueError(
            f"Record {record_number}: {field_name} must be a number"
        )

    try:
        number = float(value)

        if not math.isfinite(number) or number < 0:
            raise ValueError

        return number

    except (ValueError, TypeError):
        raise ValueError(
            f"Record {record_number}: {field_name} must be a non-negative finite number"
        )


def validate_ip(value, field_name, record_number):
    """Validate and normalize an IP address."""

    try:
        return str(ipaddress.ip_address(value.strip()))

    except (ValueError, AttributeError):
        raise ValueError(
            f"Record {record_number}: Invalid IP address in {field_name}"
        )


def normalize_records(records, dataset_type, columns):
    """Validate and normalize dataset records."""

  # Validate records using the temporary dataset schemas.
# These schemas may be updated after receiving the final ML requirements.
    if dataset_type not in DATASET_SCHEMAS:
        return records

    schema = DATASET_SCHEMAS[dataset_type]

    required_columns = schema["required"]
    optional_columns = schema["optional"]

    normalized_records = []

    for index, record in enumerate(records, start=1):

        # Check required columns in every record
        missing_columns = [
            column for column in required_columns
            if column not in record
        ]

        if missing_columns:
            raise ValueError(
                f"Record {index}: Missing required columns: "
                f"{', '.join(missing_columns)}"
            )

        normalized = {}

        # Check required values
        for field in required_columns:

            value = record[field]

            if value is None or (
                isinstance(value, str) and not value.strip()
            ):
                raise ValueError(
                    f"Record {index}: {field} cannot be empty"
                )

            if field == "timestamp":
                normalized[field] = normalize_timestamp(
                    value, index
                )

            elif (
                field in ["source_ip", "destination_ip"]
                and dataset_type in [
                    "traffic_logs",
                    "iot_logs",
                    "authorization_logs"
                ]
            ):
                normalized[field] = validate_ip(
                    value, field, index
                )

            elif dataset_type == "traffic_logs" and field == "packet_count":
                normalized[field] = normalize_integer(
                    value, field, index
                )

            elif field == "protocol":
                if not isinstance(value, str):
                    raise ValueError(
                        f"Record {index}: protocol must be text"
                    )

                normalized[field] = value.strip().upper()

            elif field == "level":
                if not isinstance(value, str):
                    raise ValueError(
                        f"Record {index}: level must be text"
                    )

                normalized[field] = value.strip().upper()
            else:
                if not isinstance(value, str):
                    raise ValueError(
                        f"Record {index}: {field} must be text"
                    )

                normalized[field] = value.strip()

              # Validate optional fields when present
        for field in optional_columns:

            if field not in record:
                normalized[field] = None
                continue

            value = record[field]

            if value is None or (
                isinstance(value, str) and not value.strip()
            ):
                normalized[field] = None
                continue

            if field == "temperature":
                normalized[field] = normalize_float(
                    value, field, index
                )

            elif field in [
                "source_port",
                "destination_port",
                "bytes_transferred"
            ]:
                number = normalize_integer(
                    value, field, index
                )

                if field in ["source_port", "destination_port"]:
                    if number > 65535:
                        raise ValueError(
                            f"Record {index}: {field} must be between 0 and 65535"
                        )

                normalized[field] = number

            elif field == "duration":
                normalized[field] = normalize_float(
                    value, field, index
                )

        # Preserve additional columns without changing their values
        for field, value in record.items():

            if field not in normalized:
                normalized[field] = (
                    value.strip()
                    if isinstance(value, str)
                    else value
                )

        normalized_records.append(normalized)

    return normalized_records


def process_uploaded_file(filename: str, file_content: bytes, dataset_type: str):
    """
    Validate, read, and normalize an uploaded CSV or JSON dataset.
    """

    # Validate dataset type
    if dataset_type not in ALLOWED_DATASET_TYPES:
        raise ValueError("Unsupported dataset type")

    # Normalize and validate the uploaded filename
    filename = normalize_filename(filename)

    # Validate file size
    if not file_content:
        raise ValueError("Uploaded file is empty")

    if len(file_content) > MAX_FILE_SIZE:
        raise ValueError("File size exceeds the 10 MB limit")

    # Validate file extension
    extension = Path(filename).suffix.lower()

    if extension not in [".csv", ".json"]:
        raise ValueError("Only CSV and JSON files are supported")
    try:
        # Read CSV files
        if extension == ".csv":

            text_content = file_content.decode("utf-8-sig")

            reader = csv.DictReader(io.StringIO(text_content))

            if not reader.fieldnames:
                raise ValueError("CSV file has no headers")

            columns = [
                name.strip() if name else ""
                for name in reader.fieldnames
            ]

            if any(not name for name in columns):
                raise ValueError("CSV contains an empty column name")

            if len(columns) != len(set(columns)):
                raise ValueError("CSV contains duplicate column names")
            reader.fieldnames = columns

            records = []

            for record in reader:
                if len(records) >= MAX_RECORDS:
                    raise ValueError(
                        f"Dataset exceeds the {MAX_RECORDS} record limit"
                    )

                records.append(record)



            if any(None in record for record in records):
                raise ValueError("CSV contains rows with extra columns")

        # Read JSON files
        else:

            text_content = file_content.decode("utf-8-sig")
            data = json.loads(text_content)

            if isinstance(data, dict):
                records = [data]

            elif isinstance(data, list):
                records = data

            else:
                raise ValueError(
                    "JSON must contain an object or a list of objects"
                )

            if not records:
                raise ValueError("JSON file contains no records")
            if len(records) > MAX_RECORDS:
                raise ValueError(
                    f"Dataset exceeds the {MAX_RECORDS} record limit"
                )
            if not all(isinstance(record, dict) for record in records):
                raise ValueError("Every JSON record must be an object")

            if any(
                not isinstance(key, str) or not key.strip()
                for record in records
                for key in record
            ):
                raise ValueError("JSON contains an empty or invalid column name")

            if any(
                key.strip() != key
                for record in records
                for key in record
            ):
                raise ValueError("JSON column names cannot contain surrounding spaces")

            columns = list(dict.fromkeys(
                key
                for record in records
                for key in record.keys()
            ))

        # Validate required columns
        if dataset_type in DATASET_SCHEMAS:

            required_columns = DATASET_SCHEMAS[dataset_type]["required"]

            missing_columns = [
                column for column in required_columns
                if column not in columns
            ]

            if missing_columns:
                raise ValueError(
                    f"Missing required columns: {', '.join(missing_columns)}"
                )

        # Normalize and validate records
        records = normalize_records(
            records,
            dataset_type,
            columns
        )

    except UnicodeDecodeError:
        raise ValueError("File must use UTF-8 encoding")

    except json.JSONDecodeError:
        raise ValueError("Invalid JSON file")

    return {
        "dataset_type": dataset_type,
        "filename": filename,
        "records_count": len(records),
        "columns": columns,
        "records": records
    }
