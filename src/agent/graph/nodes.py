from __future__ import annotations
from datetime import date as _date
from typing import Dict, Any, List, Optional
import csv

from src.agent.mcp_client import (
    kpi1, kpi2, kpi3, kpi4,
    gather_flight_data, model_endpoint,
    generate_pdf_report, send_mail,
)

from src.agent.schemas import (
    KPI1Request, KPI2Request, KPI3Request, KPI4Request
)
from src.agent.schemas import GatherFlightDataRequest, RunModelRequest
from src.agent.schemas import GeneratePDFReportRequest, SendMailRequest


class Nodes:
    """
    Nodos del flujo que usan *exclusivamente* MCP tools.
    Estado esperado (keys):
      - lista_productos: List[Dict[str, Any]]
      - buffer: Dict[str, Any]  (ej. {"flight_raw": [...]})
      - fight_type: str
      - origin: str
      - passengers: int
      - service_type: str
    """

    # -------------------------
    # Helpers
    # -------------------------
    @staticmethod
    def _load_csv(csv_path: str) -> List[Dict[str, Any]]:
        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return [{k: (v.strip() if isinstance(v, str) else v) for k, v in row.items()} for row in reader]

    @staticmethod
    def _build_payload(state: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "origin": state.get("origin"),
            "passengers": state.get("passengers"),
            "fight_type": state.get("fight_type"),
            "service_type": state.get("service_type"),
            "lista_productos": state.get("lista_productos", []),
            "context": {"flight_raw": state.get("buffer", {}).get("flight_raw")},
        }

    # -------------------------
    # Nodos (todos via MCP tools)
    # -------------------------
    @staticmethod
    def load_products(state: Dict[str, Any], csv_path: str) -> Dict[str, Any]:
        state["lista_productos"] = Nodes._load_csv(csv_path)
        return state

    @staticmethod
    def fetch_flight(
        state: Dict[str, Any],
        *,
        origin_iata: str,
        date: _date,
        airline_iata: Optional[str] = None,
        type: str = "departure",
        timeout: int = 15,
    ) -> Dict[str, Any]:
        req = GatherFlightDataRequest(
            date=date,
            iataCode=origin_iata,
            type="departure" if type not in ("departure", "arrival") else type,
            airline_iata=airline_iata,
            timeout=timeout,
        )
        flight_raw = gather_flight_data(req)  # MCP tool
        state["buffer"] = {"flight_raw": flight_raw}
        state["origin"] = origin_iata
        return state

    @staticmethod
    def define_passengers_llm(
        state: Dict[str, Any],
        *,
        origin_iata: str,
        dest_iata: str,
        flight_date: _date,
        airline_iata: Optional[str] = None,
    ) -> Dict[str, Any]:
        prompt = (
            "Eres analista de operaciones. Estima pasajeros con base en históricos y ruta.\n"
            f"Origin={origin_iata} Dest={dest_iata} Fecha={flight_date.isoformat()} Aerolínea={airline_iata or 'NA'}\n"
            "Devuelve solo un entero."
        )
        resp = model_endpoint(RunModelRequest(prompt=prompt))  # MCP tool
        # tolerante a formatos: content puede venir string o número
        content = resp.get("content", 150)
        try:
            pax = int(str(content).strip())
        except Exception:
            pax = 150
        state["passengers"] = pax
        return state

    @staticmethod
    def define_fight_type_llm(
        state: Dict[str, Any],
        *,
        origin_iata: str,
        dest_iata: str,
        flight_date: _date,
        airline_iata: Optional[str] = None,
    ) -> Dict[str, Any]:
        prompt = (
            "Clasifica el tipo de avión más probable (A320, B738, A321...).\n"
            f"Origin={origin_iata} Dest={dest_iata} Fecha={flight_date.isoformat()} Aerolínea={airline_iata or 'NA'}\n"
            "Devuelve solo el código (ej. A320)."
        )
        resp = model_endpoint(RunModelRequest(prompt=prompt))  # MCP tool
        aircraft = str(resp.get("content", "A320")).strip() or "A320"
        state["fight_type"] = aircraft
        return state

    @staticmethod
    def compute_kpis(
        state: Dict[str, Any],
        *,
        quantity_consumed: int,
        passenger_count: int,
        waste_products: List[tuple[int, int]],  # (unit_cost, quantity_wasted)
        total_cost: float,
        quantity_loaded: int,
    ) -> Dict[str, Any]:
        # Todas vía MCP KPI tools:
        r1 = kpi1(KPI1Request(quantity_consumed=quantity_consumed, passenger_count=passenger_count))
        r2 = kpi2(KPI2Request(products=waste_products))
        r3 = kpi3(KPI3Request(total_cost=total_cost, passenger_count=passenger_count))
        r4 = kpi4(KPI4Request(quantity_consumed=quantity_consumed, quantity_loaded=quantity_loaded))

        state["kpis"] = {
            "ratio_consumed_by_passenger": r1,
            "total_waste_cost": r2,
            "cost_per_passenger": r3,
            "utilization_percent": r4,
        }
        return state

    @staticmethod
    def build_payload(state: Dict[str, Any]) -> Dict[str, Any]:
        state["payload"] = Nodes._build_payload(state)
        return state

    @staticmethod
    def call_model(state: Dict[str, Any], *, purpose: str = "Optimize catering") -> Dict[str, Any]:
        payload = state.get("payload") or Nodes._build_payload(state)
        resp = model_endpoint(RunModelRequest(prompt=purpose, extra={"payload": payload}))  # MCP tool
        state["model_response"] = resp
        return state

    @staticmethod
    def make_pdf(state: Dict[str, Any], *, title: str = "Flight KPIs Report", filename: str = "report.pdf") -> Dict[str, Any]:
        kpis = state.get("kpis", {})
        path = generate_pdf_report(GeneratePDFReportRequest(title=title, kpis=kpis, filename=filename))  # MCP tool
        state["report_path"] = path
        return state

    @staticmethod
    def email_report(
        state: Dict[str, Any],
        *,
        subject: str,
        body: str,
        recipients: List[str],
        sender_email: str,
        sender_password: str,
        attachments: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        req = SendMailRequest(
            subject=subject,
            body=body,
            recipients=recipients,
            sender_email=sender_email,
            sender_password=sender_password,
            attachments=attachments or ([state["report_path"]] if state.get("report_path") else None),
        )
        result = send_mail(req)  # MCP tool
        state["email_status"] = result
        return state
