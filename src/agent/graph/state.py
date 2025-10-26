from typing import TypedDict, List, Dict, Any

class AgentState(TypedDict, total=False):
    lista_productos: List[Dict[str, Any]] 
    buffer: Dict[str, Any]                 
    fight_type: str                      
    origin: str
    passengers: int
    service_type: str                    
