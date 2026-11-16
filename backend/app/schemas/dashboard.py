from pydantic import BaseModel


class DatasetStatistics(BaseModel):
    dataset_type: str
    files_count: int
    records_count: int


class PredictionStatistics(BaseModel):
    prediction_label: str
    count: int


class FactoryStatistics(BaseModel):
    factory_id: int
    factory_name: str
    datasets_count: int
    records_count: int
    predictions_count: int


class DashboardResponse(BaseModel):
    total_datasets: int
    total_records: int
    total_network_events: int
    total_predictions: int

    datasets_by_type: list[DatasetStatistics]
    predictions_by_label: list[PredictionStatistics]
    factories: list[FactoryStatistics]