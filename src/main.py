from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timedelta
import pandas as pd

# Importaciones propias
from src.config import STATIC_DIR, TEMPLATES_DIR
from src.database import get_db
from src.services.model_service import predictor

app = FastAPI(title="Granada Smart City - Auditoría")

# --- CONFIGURACIÓN ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# --- MODELOS DE DATOS (PYDANTIC) ---

class AuditRequest(BaseModel):
    start_date: str  # Formato ISO
    end_date: str
    zone_name: str

class DashboardFilter(BaseModel):
    zone_name: str
    start_date: str
    end_date: str

# --- RUTAS DE NAVEGACIÓN ---

@app.get("/")
async def root():
    """
    Redirección automática: 
    Al entrar en la raíz, te manda al Dashboard.
    """
    return RedirectResponse(url="/dashboard")

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    """
    Carga la estructura del Dashboard (vacía para que cargue rápido).
    Los datos se piden después vía API.
    """
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "avg_consumption": 0,
        "max_consumption": 0,
        "chart_labels": [],
        "chart_values": []
    })

@app.get("/prediction", response_class=HTMLResponse)
async def prediction_page(request: Request):
    """Carga el simulador/auditoría vacío."""
    return templates.TemplateResponse("prediction.html", {"request": request})

# --- ENDPOINTS API (LÓGICA) ---

@app.get("/api/zones")
def get_zones(db: Session = Depends(get_db)):
    """Obtiene la lista de zonas ordenada alfabéticamente."""
    try:
        res = db.execute(text("SELECT DISTINCT zone_name FROM consumo_granada ORDER BY zone_name ASC")).fetchall()
        return {"zones": [r[0] for r in res]}
    except:
        return {"zones": []}

@app.post("/api/audit")
async def audit_model(request: AuditRequest, db: Session = Depends(get_db)):
    """
    Versión Híbrida Inteligente para la página de PREDICCIÓN:
    - Si hay datos históricos (Pasado) -> Auditoría (Real vs IA).
    - Si NO hay datos (Futuro) -> Simulación Pura (Solo IA).
    """
    try:
        start = pd.to_datetime(request.start_date)
        end = pd.to_datetime(request.end_date)
        
        # Validaciones
        if (end - start).days > 7:
            raise HTTPException(status_code=400, detail="El rango máximo permitido es de 7 días.")
        if start >= end:
            raise HTTPException(status_code=400, detail="La fecha fin debe ser posterior a la de inicio.")

        # 1. Intentamos buscar datos REALES (Pasado)
        query_line = text("""
            SELECT timestamp, consumption_kwh, temperature 
            FROM consumo_granada 
            WHERE zone_name = :zone 
              AND timestamp >= :start 
              AND timestamp <= :end
            ORDER BY timestamp ASC
        """)
        
        rows = db.execute(query_line, {"zone": request.zone_name, "start": start, "end": end}).fetchall()

        labels = []
        real_data = []
        ai_data = []
        is_future = False

        if rows:
            # CASO A: TENEMOS DATOS (AUDITORÍA)
            for row in rows:
                ts = row[0]
                labels.append(ts.strftime("%d/%m %H:%M"))
                real_data.append(row[1]) # Dato Real
                
                # Predicción IA usando temperatura real histórica
                pred = predictor.predict(str(ts), request.zone_name, float(row[2]))
                ai_data.append(pred)
        else:
            # CASO B: NO HAY DATOS (FUTURO / SIMULACIÓN)
            is_future = True
            
            # Generamos el rango de fechas hora a hora nosotros mismos
            current = start
            while current <= end:
                labels.append(current.strftime("%d/%m %H:%M"))
                real_data.append(None) # No hay dato real
                
                # Temp estimada fija para simulación rápida (o llamar a API externa)
                temp_estimada = 15.0 
                
                pred = predictor.predict(str(current), request.zone_name, temp_estimada)
                ai_data.append(pred)
                
                current += timedelta(hours=1)

        # 2. Gráfico de Barras (Ranking)
        bar_labels = []
        bar_values = []
        
        if not is_future:
            query_bar = text("""
                SELECT zone_name, SUM(consumption_kwh) as total
                FROM consumo_granada
                WHERE timestamp >= :start AND timestamp <= :end
                GROUP BY zone_name
                ORDER BY zone_name ASC
            """)
            rows_bar = db.execute(query_bar, {"start": start, "end": end}).fetchall()
            bar_labels = [r[0] for r in rows_bar]
            bar_values = [round(r[1], 2) for r in rows_bar]

        return {
            "status": "success",
            "is_future": is_future,
            "line_chart": { "labels": labels, "real": real_data, "ai": ai_data },
            "bar_chart": { "labels": bar_labels, "values": bar_values }
        }

    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": str(e)})

@app.post("/api/dashboard/update")
async def update_dashboard(request: DashboardFilter, db: Session = Depends(get_db)):
    """
    Calcula KPIs y datos para el gráfico del DASHBOARD.
    """
    try:
        start = pd.to_datetime(request.start_date)
        end = pd.to_datetime(request.end_date)
        
        # Validación de 7 días
        if (end - start).days > 7:
            raise HTTPException(status_code=400, detail="Por rendimiento, selecciona un máximo de 7 días.")
        if start >= end:
            raise HTTPException(status_code=400, detail="La fecha fin debe ser posterior a la de inicio.")

        # Consulta SQL Principal
        query = text("""
            SELECT timestamp, consumption_kwh, temperature 
            FROM consumo_granada 
            WHERE zone_name = :zone 
              AND timestamp >= :start 
              AND timestamp <= :end
            ORDER BY timestamp ASC
        """)
        
        rows = db.execute(query, {"zone": request.zone_name, "start": start, "end": end}).fetchall()

        if not rows:
            raise HTTPException(status_code=404, detail="No hay datos para esta selección.")

        # Procesar datos
        timestamps = []
        consumptions = []
        temperatures = []
        
        for row in rows:
            timestamps.append(row[0].strftime("%d/%m %H:%M"))
            consumptions.append(float(row[1]) if row[1] is not None else 0)
            temperatures.append(float(row[2]) if row[2] is not None else 0)

        # CÁLCULO DE KPIS
        total_consumo = sum(consumptions)
        promedio_hora = total_consumo / len(consumptions) if consumptions else 0
        temp_media = sum(temperatures) / len(temperatures) if temperatures else 0
        pico_maximo = max(consumptions) if consumptions else 0

        return {
            "status": "success",
            "kpis": {
                "total_consumo": f"{total_consumo:,.2f}",
                "promedio_hora": f"{promedio_hora:.2f}",
                "temp_media": f"{temp_media:.1f}",
                "pico_maximo": f"{pico_maximo:.2f}"
            },
            "chart": {
                "labels": timestamps,
                "consumption": consumptions,
                "temperature": temperatures
            }
        }

    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": str(e)})

@app.get("/health")
def health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok", "model": True}
    except:
        return {"status": "error"}