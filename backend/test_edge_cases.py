from app.services.data_ingestion_service import process_uploaded_file

tests = [
    {
        "name": "Invalid timestamp",
        "filename": "invalid_date.csv",
        "type": "traffic_logs",
        "data": b"timestamp,source_ip,destination_ip,protocol,packet_count\ninvalid-date,192.168.1.10,192.168.1.20,TCP,100"
    },
    {
        "name": "Empty required field",
        "filename": "empty_field.csv",
        "type": "traffic_logs",
        "data": b"timestamp,source_ip,destination_ip,protocol,packet_count\n2026-11-05,,192.168.1.20,TCP,100"
    },
    {
        "name": "Duplicate column names",
        "filename": "duplicate_columns.csv",
        "type": "traffic_logs",
        "data": b"timestamp,source_ip,source_ip,protocol,packet_count\n2026-11-05,192.168.1.10,192.168.1.20,TCP,100"
    },
    {
        "name": "Invalid JSON",
        "filename": "invalid.json",
        "type": "traffic_logs",
        "data": b'{"timestamp": "2026-11-05", "source_ip": '
    },
    {
        "name": "Empty file",
        "filename": "empty.csv",
        "type": "traffic_logs",
        "data": b""
    }
]

passed = 0

for test in tests:
    try:
        process_uploaded_file(
            filename=test["filename"],
            file_content=test["data"],
            dataset_type=test["type"]
        )

        print("FAILED:", test["name"], "- Invalid data was accepted")

    except ValueError as error:
        print("PASSED:", test["name"])
        print("Reason:", error)
        passed += 1

print(f"\nResults: {passed}/{len(tests)} tests passed")
