# src/utils.py
from __future__ import annotations
from datetime import date as _date
from typing import Literal, Optional, Dict, Any, List
import os
import requests

from src.settings import get_settings 

def _get_base_url() -> str:
    s = get_settings()
    url = s.future_flights_url or os.getenv("FUTURE_FLIGHTS_URL")
    if not url:
        raise RuntimeError("FUTURE_FLIGHTS_URL no está configurada.")
    return url

def _get_api_key() -> str:
    s = get_settings()
    key = s.aviation_edge_api or os.getenv("AVIATION_EDGE_API")
    if not key:
        raise RuntimeError("AVIATION_EDGE_API no está configurada.")
    return key

class GetFlightsData:
    @staticmethod
    def get_data(
        date: _date,
        iataCode: str,
        type: Literal["departure", "arrival"] = "departure",
        *,
        airline_iata: Optional[str] = None,
        airline_icao: Optional[str] = None,
        flight_num: Optional[str] = None,
        timeout: int = 15,
    ) -> List[Dict[str, Any]]:
        if type not in ("departure", "arrival"):
            raise ValueError('type debe ser "departure" o "arrival".')

        base_url = _get_base_url()
        key = _get_api_key()

        params: Dict[str, Any] = {
            "key": key,
            "type": type,
            "iataCode": iataCode.upper().strip(),
            "date": date.isoformat(),
        }
        if airline_iata:
            params["airline_iata"] = airline_iata.upper().strip()
        if airline_icao:
            params["airline_icao"] = airline_icao.upper().strip()
        if flight_num:
            params["flight_num"] = str(flight_num).strip()

        try:
            resp = requests.get(base_url, params=params, timeout=timeout)
            resp.raise_for_status()
        except requests.RequestException as exc:
            raise RuntimeError(f"Error de red al llamar a Aviation Edge: {exc}") from exc

        data = resp.json()
        if isinstance(data, dict) and data.get("error"):
            raise RuntimeError(f"API error: {data.get('error')}")
        if not isinstance(data, list):
            raise RuntimeError(f"Respuesta inesperada: {str(data)[:300]}")

        return data
