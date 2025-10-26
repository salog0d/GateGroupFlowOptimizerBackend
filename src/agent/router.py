from __future__ import annotations
from datetime import date as _date
from pathlib import Path
from typing import Optional, Dict, Any, List

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel, Field
from src.agent.graph.workflow import run_workflow

agent_router = APIRouter(prefix="/api/agent", tags=["Agent"])


# -------------------------------
# Esquemas (JSON)
# -------------------------------
class ComputeKpisOpts(BaseModel):
    quantity_consumed: int = 0
    passenger_count: Optional[int] = None  # si no viene, se usa state["passengers"]
    waste_products: List[tuple[int, int]] = Field(default_factory=list)  # [(unit_cost, qty_wasted), ...]
    total_cost: float = 0.0
    quantity_loaded: int = 1

class EmailOpts(BaseModel):
    subject: str
    body: Optional[str] = "Attached report."
    recipients: List[str]
    sender_email: str
    sender_password: str
    attachments: Optional[List[str]] = None

class WorkflowRequest(BaseModel):
    csv_path: str
    origin_iata: str
    dest_iata: str
    flight_date: _date
    airline_iata: Optional[str] = None
    service_type: str = "standard"
    use_llm_passengers: bool = True
    use_llm_fight_type: bool = True
    compute_kpis_opts: Optional[ComputeKpisOpts] = None
    make_pdf: bool = True
    email_opts: Optional[EmailOpts] = None

class WorkflowResponse(BaseModel):
    state: Dict[str, Any]


# -------------------------------
# Endpoint JSON (ruta local del CSV)
# -------------------------------
@agent_router.post("/run", response_model=WorkflowResponse)
def run_agent(req: WorkflowRequest) -> WorkflowResponse:
    csv_path = Path(req.csv_path)
    if not csv_path.exists() or csv_path.suffix.lower() != ".csv":
        raise HTTPException(status_code=400, detail="CSV inválido o no encontrado.")

    state = run_workflow(
        csv_path=str(csv_path),
        origin_iata=req.origin_iata,
        dest_iata=req.dest_iata,
        flight_date=req.flight_date,
        airline_iata=req.airline_iata,
        service_type=req.service_type,
        use_llm_passengers=req.use_llm_passengers,
        use_llm_fight_type=req.use_llm_fight_type,
        compute_kpis_opts=(req.compute_kpis_opts.model_dump() if req.compute_kpis_opts else None),
        make_pdf=req.make_pdf,
        email_opts=(req.email_opts.model_dump() if req.email_opts else None),
    )
    return WorkflowResponse(state=state)


# -------------------------------
# Endpoint Multipart (subida de CSV)
# -------------------------------
@agent_router.post("/run-multipart", response_model=WorkflowResponse)
async def run_agent_multipart(
    file: UploadFile = File(..., description="CSV de productos"),
    origin_iata: str = Form(...),
    dest_iata: str = Form(...),
    flight_date: str = Form(...),  # YYYY-MM-DD
    airline_iata: Optional[str] = Form(None),
    service_type: str = Form("standard"),
    use_llm_passengers: bool = Form(True),
    use_llm_fight_type: bool = Form(True),
    # Campos opcionales para KPIs (puedes ampliarlos si quieres)
    kpi_quantity_consumed: int = Form(0),
    kpi_passenger_count: Optional[int] = Form(None),
    kpi_total_cost: float = Form(0.0),
    kpi_quantity_loaded: int = Form(1),
    make_pdf: bool = Form(True),
) -> WorkflowResponse:
    # Validaciones básicas de archivo
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="El archivo debe ser .csv")

    # Guardar temporalmente
    tmp_dir = Path("tmp")
    tmp_dir.mkdir(exist_ok=True)
    tmp_path = tmp_dir / f"upload_{file.filename}"
    content = await file.read()
    tmp_path.write_bytes(content)

    # Parse flight_date
    try:
        year, month, day = map(int, flight_date.split("-"))
        fdate = _date(year, month, day)
    except Exception:
        raise HTTPException(status_code=400, detail="flight_date debe ser YYYY-MM-DD")

    # Opciones KPIs mínimas (waste_products vacío por default)
    compute_kpis_opts = {
        "quantity_consumed": int(kpi_quantity_consumed),
        "passenger_count": (int(kpi_passenger_count) if kpi_passenger_count is not None else None),
        "waste_products": [],  # puedes mapear desde otro campo si lo pasas
        "total_cost": float(kpi_total_cost),
        "quantity_loaded": int(kpi_quantity_loaded),
    }

    # Ejecutar workflow
    state = run_workflow(
        csv_path=str(tmp_path),
        origin_iata=origin_iata,
        dest_iata=dest_iata,
        flight_date=fdate,
        airline_iata=airline_iata,
        service_type=service_type,
        use_llm_passengers=use_llm_passengers,
        use_llm_fight_type=use_llm_fight_type,
        compute_kpis_opts=compute_kpis_opts,
        make_pdf=make_pdf,
        email_opts=None,  # si quieres enviar correo aquí, agrega campos Form y pásalos
    )
    return WorkflowResponse(state=state)
