"""
Router para Predicción - Sistema Principal.
Permite hacer predicciones automáticas obteniendo la temperatura desde APIs.
Usuario solo envía timestamp y zona.
"""
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from src.models.schemas import PredictionInput, PredictionOutput, ZonesResponse
from src.loader import get_prediction, is_model_loaded
from src.services.historical_service import get_available_zones
from src.config import TEMPLATES_DIR

router = APIRouter()
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("/", response_class=HTMLResponse)
async def prediction_view(request: Request):
    """
    Renderiza la página del simulador de predicción (HTML).
    """
    return templates.TemplateResponse("prediction.html", {"request": request})


@router.post("/api/predict", response_model=PredictionOutput)
async def predict_consumption(input_data: PredictionInput):
    """
    Endpoint API: Realiza una predicción de consumo energético.
    La temperatura se obtiene automáticamente.
    
    Body JSON:
    {
        "timestamp": "2025-12-25T20:00:00",
        "zone_name": "ALBAICIN"
    }
    
    Retorna:
    {
        "prediction": 1234.56,
        "timestamp": "2025-12-25T20:00:00",
        "zone_name": "ALBAICIN",
        "temperature": 4.5,
        "temperature_source": "open-meteo"
    }
    """
    # Verificar que el modelo esté cargado
    if not is_model_loaded():
        raise HTTPException(
            status_code=503,
            detail="El modelo de predicción no está disponible. Verifica que el archivo del modelo exista."
        )
    
    # Llamar al loader con los datos simplificados
    result, status_code = await get_prediction(
        timestamp_str=input_data.timestamp,
        zone_name=input_data.zone_name
    )
    
    # Si hay error, lanzar excepción HTTP
    if status_code != 200:
        raise HTTPException(status_code=status_code, detail=result.get("error"))
    
    return result


@router.get("/api/zones", response_model=ZonesResponse)
async def get_zones():
    """
    Endpoint API: Devuelve la lista de zonas disponibles.
    Nombres coinciden con PostgreSQL (minúsculas con guiones bajos).
    
    Retorna:
    {
        "zones": ["albaicin_alto", "centro_catedral", "pts_tecnologico", ...],
        "count": 20
    }
    """
    # Zonas exactas de PostgreSQL (orden alfabético según las features del modelo)
    zones = [
        'albaicin_alto', 'albaicin_bajo', 'bola_de_oro', 'camino_ronda',
        'cartuja', 'centro_catedral', 'cervantes', 'chana_barrio',
        'chana_bobadilla', 'fuentenueva', 'mercagranada', 'norte_almanjayar',
        'pedro_antonio', 'periodistas', 'plaza_toros', 'pts_tecnologico',
        'realejo', 'sacromonte', 'zaidin_nuevo', 'zaidin_vergeles'
    ]
    return {
        "zones": zones,
        "count": len(zones)
    }


@router.get("/api/model-status")
async def model_status():
    """
    Health check del modelo.
    Verifica si el modelo está cargado y listo para predicciones.
    """
    loaded = is_model_loaded()
    return {
        "model_loaded": loaded,
        "status": "ready" if loaded else "not_available",
        "message": "Modelo listo para predicciones" if loaded else "Modelo no cargado. Coloca el archivo .joblib en database/models/"
    }

