
from sqlalchemy.orm import Session

from app.models.network_event import NetworkEvent


def get_company_network_events(
    db: Session,
    company_id: int
):
    """
    Retrieve all network events belonging to a specific company.
    """

    events = db.query(NetworkEvent).filter(
        NetworkEvent.company_id == company_id
    ).order_by(
        NetworkEvent.created_at.desc()
    ).all()

    return events

def prepare_network_event_features(events):
    """
    Convert network events into numerical features
    suitable for Machine Learning models.
    """

    prepared_data = []

    for event in events:

        packet_count = event.packet_count or 0
        bytes_transferred = event.bytes_transferred or 0
        duration = event.duration or 0

        # Calculate network traffic rates
        bytes_per_packet = (
            bytes_transferred / packet_count
            if packet_count > 0 else 0
        )

        packets_per_second = (
            packet_count / duration
            if duration > 0 else 0
        )

        bytes_per_second = (
            bytes_transferred / duration
            if duration > 0 else 0
        )

        protocol = (event.protocol or "").upper()

        features = {
            "source_port": event.source_port or 0,
            "destination_port": event.destination_port or 0,
            "packet_count": packet_count,
            "bytes_transferred": bytes_transferred,
            "duration": duration,
            "protocol_tcp": 1 if protocol == "TCP" else 0,
            "protocol_udp": 1 if protocol == "UDP" else 0,
            "protocol_icmp": 1 if protocol == "ICMP" else 0,
            "protocol_other": 1 if protocol not in ["TCP", "UDP", "ICMP"] else 0,
            "bytes_per_packet": bytes_per_packet,
            "packets_per_second": packets_per_second,
            "bytes_per_second": bytes_per_second
        }

        prepared_data.append(features)

    return prepared_data
