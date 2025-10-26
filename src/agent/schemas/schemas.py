from pydantic import BaseModel, EmailStr
from typing import List, Tuple, Optional, Literal, TypedDict, Dict
from datetime import date as _date

class KPI1Request(BaseModel):
    """Ratio consumido por pasajero"""
    quantity_consumed: int 
    passenger_count: int 


class KPI2Request(BaseModel):
    """Costo total de desperdicio"""
    products: List[Tuple[int, int]]


class KPI3Request(BaseModel):
    """Costo por pasajero"""
    total_cost: float 
    passenger_count: int 


class KPI4Request(BaseModel):
    """Tasa de utilización por pasajero"""
    quantity_consumed: int 
    quantity_loaded: int 


class GatherFlightDataInput(TypedDict, total=False):
    date: _date
    iataCode: str
    type: Literal["departure", "arrival"]
    airline_iata: Optional[str]
    airline_icao: Optional[str]
    flight_num: Optional[str]
    timeout: int

class GeneratePDFReportRequest(BaseModel):
    """Entrada para generate_pdf_report"""
    title: str
    kpis: Dict[str, float]
    filename: Optional[str] = "report.pdf"


class SendMailRequest(BaseModel):
    """Entrada para send_mail"""
    subject: str
    body: str
    recipients: List[EmailStr]
    sender_email: EmailStr
    sender_password: str
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    attachments: Optional[List[str]] = None

