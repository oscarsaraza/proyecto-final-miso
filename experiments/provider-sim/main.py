"""Simulador del proveedor de Open Finance: latencia y tasa de error configurables."""
import asyncio
import os
import random

from fastapi import FastAPI, HTTPException

LATENCIA_MS = int(os.getenv("LATENCY_MS", "50"))
TASA_ERROR = float(os.getenv("ERROR_RATE", "0"))

app = FastAPI(title="Simulador Open Finance")


@app.get("/profile/{cliente_id}")
async def perfil(cliente_id: str) -> dict:
    await asyncio.sleep(LATENCIA_MS / 1000)
    if random.random() < TASA_ERROR:
        raise HTTPException(status_code=503, detail="proveedor no disponible")
    return {"score": 700, "nivel": "bajo", "fuente": "open-finance-simulado"}
