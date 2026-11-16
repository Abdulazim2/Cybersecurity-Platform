import pytest

from app.schemas.network_event import NetworkEventCreate


def valid_event_data():
    return {
        "factory_id": 1,
        "source_ip": "192.168.1.10",
        "destination_ip": "192.168.1.20",
        "protocol": "TCP"
    }


def test_network_event_rejects_empty_protocol():
    data = valid_event_data()
    data["protocol"] = ""

    with pytest.raises(ValueError):
        NetworkEventCreate(**data)


def test_network_event_rejects_whitespace_protocol():
    data = valid_event_data()
    data["protocol"] = "   "

    with pytest.raises(ValueError):
        NetworkEventCreate(**data)


@pytest.mark.parametrize("duration", [
    float("nan"),
    float("inf"),
    float("-inf")
])
def test_network_event_rejects_non_finite_duration(duration):
    data = valid_event_data()
    data["duration"] = duration

    with pytest.raises(ValueError):
        NetworkEventCreate(**data)


def test_network_event_normalizes_protocol():
    data = valid_event_data()
    data["protocol"] = "tcp"

    event = NetworkEventCreate(**data)

    assert event.protocol == "TCP"