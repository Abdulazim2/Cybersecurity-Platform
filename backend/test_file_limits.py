from app.services.data_ingestion_service import process_uploaded_file

tests = [
    {
        "name": "Unsupported extension",
        "filename": "test.txt",
        "data": b"some test data"
    },
    {
        "name": "File exceeds 10 MB",
        "filename": "large.csv",
        "data": b"x" * (10 * 1024 * 1024 + 1)
    }
]

for test in tests:
    try:
        process_uploaded_file(
            filename=test["filename"],
            file_content=test["data"],
            dataset_type="traffic_logs"
        )
        print("FAILED:", test["name"])

    except ValueError as error:
        print("PASSED:", test["name"])
        print("Reason:", error)

print("\nFile size and extension tests completed!")
