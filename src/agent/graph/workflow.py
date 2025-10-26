from __future__ import annotations
from datetime import date as _date
from typing import Dict, Any, Optional

from src.agent.graph.nodes import Nodes


def run_workflow(
    *,
    csv_path: str,
    origin_iata: str,
    dest_iata: str,
    flight_date: _date,
    airline_iata: Optional[str] = None,
    service_type: str = "standard",
    # toggles
    use_llm_passengers: bool = True,
    use_llm_fight_type: bool = True,
    compute_kpis_opts: Optional[Dict[str, Any]] = None,
    make_pdf: bool = True,
    email_opts: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Orquesta TODO vía tus MCP tools.
    Devuelve el estado final con payload, KPIs, respuesta del modelo, etc.
    """
    state: Dict[str, Any] = {}

    # 1) CSV → lista_productos
    state = Nodes.load_products(state, csv_path)

    # 2) AviationEdge → buffer.flight_raw + origin
    state = Nodes.fetch_flight(
        state,
        origin_iata=origin_iata,
        date=flight_date,
        airline_iata=airline_iata,
        type="departure",
        timeout=15,
    )

    # 3) Pasajeros (LLM via MCP model_endpoint)
    state = Nodes.define_passengers_llm(
        state,
        origin_iata=origin_iata,
        dest_iata=dest_iata,
        flight_date=flight_date,
        airline_iata=airline_iata,
    ) if use_llm_passengers else state

    # 4) fight_type (LLM via MCP model_endpoint)
    state = Nodes.define_fight_type_llm(
        state,
        origin_iata=origin_iata,
        dest_iata=dest_iata,
        flight_date=flight_date,
        airline_iata=airline_iata,
    ) if use_llm_fight_type else state

    # 5) service_type
    state = Nodes.set_service_type(state, service_type)

    # 6) KPIs (opcional)
    if compute_kpis_opts:
        state = Nodes.compute_kpis(
            state,
            quantity_consumed=compute_kpis_opts.get("quantity_consumed", 0),
            passenger_count=compute_kpis_opts.get("passenger_count", state.get("passengers", 0)),
            waste_products=compute_kpis_opts.get("waste_products", []),
            total_cost=compute_kpis_opts.get("total_cost", 0.0),
            quantity_loaded=compute_kpis_opts.get("quantity_loaded", 1),
        )

    # 7) Payload para el endpoint ML
    state = Nodes.build_payload(state)

    # 8) Llamar al modelo ML (endpoint) vía MCP
    state = Nodes.call_model(state, purpose="Optimize catering")

    # 9) PDF (opcional)
    if make_pdf:
        state = Nodes.make_pdf(
            state,
            title="Flight KPIs Report",
            filename="report.pdf",
        )

    # 10) Email (opcional)
    if email_opts:
        state = Nodes.email_report(
            state,
            subject=email_opts["subject"],
            body=email_opts.get("body", "Attached report."),
            recipients=email_opts["recipients"],
            sender_email=email_opts["sender_email"],
            sender_password=email_opts["sender_password"],
            attachments=email_opts.get("attachments"),
        )

    return state