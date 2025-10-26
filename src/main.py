# main.py
from __future__ import annotations

from datetime import date as _date, datetime
from typing import Literal, Optional, Any, Dict, List

from fastapi import FastAPI, HTTPException, Query

from src.inventory.router import (
    products_router,
    lotes_router,
    lot_items_router,
    assignments_router,
)

from src.utils import GetFlightsData

app = FastAPI(
    title="GateGroup Agentic CRM API",
    version="1.0.0",
    description="API for managing catering lots, products, and assignments",
)

app.include_router(products_router)
app.include_router(lotes_router)
app.include_router(lot_items_router)
app.include_router(assignments_router)


@app.get("/", tags=["root"])
async def root():
    return {"message": "Catering Inventory API is running"}


@app.get("/api/flights/future", tags=["flights"], response_model=List[Dict[str, Any]])
def get_future_flights(
    date: _date = Query(..., description="Fecha futura en formato YYYY-MM-DD."),
    iataCode: str = Query(..., min_length=3, max_length=3, description="Código IATA del aeropuerto (ej. BER)"),
    type: Literal["departure", "arrival"] = Query("departure", description="Tipo de horario a consultar"),
    airline_iata: Optional[str] = Query(None, description="Filtro por IATA de aerolínea (ej. LH)"),
    airline_icao: Optional[str] = Query(None, description="Filtro por ICAO de aerolínea (ej. DLH)"),
    flight_num: Optional[str] = Query(None, description="Número de vuelo sin prefijo de aerolínea (ej. 6258)"),
) -> List[Dict[str, Any]]:
    """
    Proxy al endpoint flightsFuture de Aviation Edge con validaciones básicas.
    """
    today = datetime.utcnow().date()
    if date <= today:
        raise HTTPException(status_code=400, detail="La fecha debe ser futura (mañana en adelante).")

    if not iataCode.isalpha():
        raise HTTPException(status_code=400, detail="iataCode inválido; usa solo letras (p. ej., 'BER').")

    try:
        data = GetFlightsData.get_data(
            date=date,
            iataCode=iataCode,
            type=type,
            airline_iata=airline_iata,
            airline_icao=airline_icao,
            flight_num=flight_num,
        )
        return data
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve)) from ve
    except RuntimeError as re:
        raise HTTPException(status_code=502, detail=str(re)) from re
