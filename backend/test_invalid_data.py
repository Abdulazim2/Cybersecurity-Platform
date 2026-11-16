
import pytest

from app.services.data_ingestion_service import process_uploaded_file


@pytest.mark.parametrize(
    "name, data, expected_error",
    [
        (
            "Invalid IP",
            b"timestamp,source_ip,destination_ip,protocol,packet_count\n2026-11-05,999.999.1.1,192.168.1.20,TCP,100",
            "Invalid IP address",
        ),
        (
            "Negative packet count",
            b"timestamp,source_ip,destination_ip,protocol,packet_count\n2026-11-05,192.168.1.10,192.168.1.20,TCP,-10",
            "packet_count",
        ),
        (
            "Invalid port",
            b"timestamp,source_ip,destination_ip,protocol,packet_count,source_port\n2026-11-05,192.168.1.10,192.168.1.20,TCP,100,70000",
            "source_port",
        ),
        (
            "Missing required column",
            b"timestamp,source_ip,protocol,packet_count\n2026-11-05,192.168.1.10,TCP,100",
            "Missing required columns",
        ),
    ],
)
def test_invalid_traffic_data(name, data, expected_error):
    with pytest.raises(ValueError, match=expected_error):
        process_uploaded_file(
            filename="invalid_test.csv",
            file_content=data,
            dataset_type="traffic_logs",
        )
