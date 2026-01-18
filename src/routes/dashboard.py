"""
Rutas para el dashboard - Visualización de datos de consumo energético con filtros
"""

from fastapi import APIRouter, Request, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
from datetime import datetime
from decimal import Decimal
import sys
import os
import json

# Agregar el directorio padre al path para importar database
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from database import execute_query

router = APIRouter()
templates = Jinja2Templates(directory="src/templates")


def decimal_to_float(obj):
    """Convierte Decimal a float, datetime a ISO string para serialización JSON"""
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: decimal_to_float(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [decimal_to_float(i) for i in obj]
    return obj


def get_zonas_disponibles():
    """Retorna la lista de zonas disponibles"""
    zonas = [
        "albaicin_alto",
        "albaicin_bajo",
        "bola_de_oro",
        "camino_ronda",
        "cartuja",
        "centro_catedral",
        "cervantes",
        "chana_barrio",
        "chana_bobadilla",
        "fuentenueva",
        "mercagranada",
        "norte_almanjayar",
        "pedro_antonio",
        "periodistas",
        "plaza_toros",
        "pts_tecnologico",
        "realejo",
        "sacromonte",
        "zaidin_nuevo",
        "zaidin_vergeles",
    ]
    return [{"value": z, "label": z.replace("_", " ").title()} for z in zonas]


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """
    Página principal del dashboard con filtros interactivos
    """
    try:
        # Obtener zonas disponibles
        zonas = get_zonas_disponibles()

        context = {"request": request, "zonas": zonas}

        return templates.TemplateResponse("dashboard.html", context)

    except Exception as e:
        print(f"Error en la ruta dashboard: {e}")
        return templates.TemplateResponse(
            "dashboard.html", {"request": request, "error": str(e), "zonas": []}
        )


@router.get("/api/dashboard/filtrar")
async def filtrar_datos(
    zona: str = Query(..., description="Zona seleccionada"),
    anio_inicio: int = Query(..., description="Año de inicio (2015-2025)"),
    mes_inicio: int = Query(..., description="Mes de inicio (1-12)"),
    dia_inicio: int = Query(..., description="Día de inicio (1-31)"),
    hora_inicio: int = Query(..., description="Hora de inicio (0-23)"),
    anio_fin: int = Query(..., description="Año de fin (2015-2025)"),
    mes_fin: int = Query(..., description="Mes de fin (1-12)"),
    dia_fin: int = Query(..., description="Día de fin (1-31)"),
    hora_fin: int = Query(..., description="Hora de fin (0-23)"),
):
    """
    API endpoint para obtener datos filtrados del dashboard
    """
    try:
        # Validar zona
        zona_column = f"zona_{zona}"

        # Construir timestamps de inicio y fin
        timestamp_inicio = f"{anio_inicio:04d}-{mes_inicio:02d}-{dia_inicio:02d} {hora_inicio:02d}:00:00"
        timestamp_fin = (
            f"{anio_fin:04d}-{mes_fin:02d}-{dia_fin:02d} {hora_fin:02d}:00:00"
        )

        # Cláusula WHERE simplificada usando timestamp
        where_clause = f"""
            {zona_column} = 1
            AND timestamp BETWEEN %s AND %s
        """
        params = (timestamp_inicio, timestamp_fin)

        # Consulta para obtener los KPIs
        kpis_query = f"""
            SELECT 
                SUM(consumption_kwh) as consumo_total,
                AVG(consumption_kwh) as consumo_promedio,
                SUM(consumption_kwh) / NULLIF(COUNT(DISTINCT EXTRACT(HOUR FROM timestamp)), 0) as total_por_hora,
                AVG(temperature) as temperatura_media,
                MAX(consumption_kwh) as pico_maximo,
                COUNT(*) as total_registros
            FROM consumo_granada
            WHERE {where_clause};
        """

        kpis = execute_query(kpis_query, params, fetch_one=True)

        # Consulta para consumo por hora (usando EXTRACT para obtener la hora del timestamp)
        consumo_hora_query = f"""
            SELECT 
                EXTRACT(HOUR FROM timestamp)::INTEGER as hour,
                SUM(consumption_kwh) as consumo_total
            FROM consumo_granada
            WHERE {where_clause}
            GROUP BY EXTRACT(HOUR FROM timestamp)
            ORDER BY hour;
        """

        consumo_por_hora = execute_query(consumo_hora_query, params)

        # Consulta para consumo por TODAS las zonas (OPTIMIZADA: 1 sola query en vez de 20)
        zonas_list = [
            "albaicin_alto",
            "albaicin_bajo",
            "bola_de_oro",
            "camino_ronda",
            "cartuja",
            "centro_catedral",
            "cervantes",
            "chana_barrio",
            "chana_bobadilla",
            "fuentenueva",
            "mercagranada",
            "norte_almanjayar",
            "pedro_antonio",
            "periodistas",
            "plaza_toros",
            "pts_tecnologico",
            "realejo",
            "sacromonte",
            "zaidin_nuevo",
            "zaidin_vergeles",
        ]

        # Cláusula WHERE sin filtro de zona (usa los mismos timestamps)
        where_clause_sin_zona = "timestamp BETWEEN %s AND %s"

        # UNA SOLA QUERY que calcula todas las zonas a la vez usando CASE WHEN
        zona_sum_cases = ",\n                ".join(
            [
                f"SUM(CASE WHEN zona_{z} = 1 THEN consumption_kwh ELSE 0 END) as {z}"
                for z in zonas_list
            ]
        )

        todas_zonas_query = f"""
            SELECT 
                {zona_sum_cases}
            FROM consumo_granada
            WHERE {where_clause_sin_zona};
        """

        resultado_zonas = execute_query(todas_zonas_query, params, fetch_one=True)

        # Construir lista de consumo por zona
        consumo_por_zona = []
        for zona_nombre in zonas_list:
            consumo = resultado_zonas.get(zona_nombre)
            if consumo and consumo > 0:
                consumo_por_zona.append(
                    {
                        "zona": zona_nombre.replace("_", " ").title(),
                        "consumo_total": float(consumo),
                    }
                )

        # Ordenar alfabéticamente por nombre de zona
        consumo_por_zona.sort(key=lambda x: x["zona"])

        # Consulta para consumo y temperatura por hora (agrupado por timestamp)
        consumo_temp_hora_query = f"""
            SELECT 
                timestamp,
                AVG(consumption_kwh) as consumo_promedio,
                AVG(temperature) as temperatura_promedio
            FROM consumo_granada
            WHERE {where_clause}
            GROUP BY timestamp
            ORDER BY timestamp
            LIMIT 168;
        """

        consumo_temp_por_hora = execute_query(consumo_temp_hora_query, params)

        # Convertir todos los Decimals a float para JSON
        return JSONResponse(
            {
                "success": True,
                "kpis": decimal_to_float(kpis),
                "consumo_por_hora": decimal_to_float(consumo_por_hora),
                "consumo_por_zona": consumo_por_zona,  # TODAS las zonas
                "consumo_temp_por_hora": decimal_to_float(consumo_temp_por_hora),
                "zona": zona.replace("_", " ").title(),
                "periodo": f"{anio_inicio}/{mes_inicio:02d}/{dia_inicio:02d} {hora_inicio:02d}:00 - {anio_fin}/{mes_fin:02d}/{dia_fin:02d} {hora_fin:02d}:00",
            }
        )

    except Exception as e:
        print(f"Error al filtrar datos: {e}")
        import traceback

        traceback.print_exc()
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)
