from fastapi import FastAPI
from src.inventory.router import (
    products_router,
    lotes_router,
    lot_items_router,
    assignments_router,
)

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
