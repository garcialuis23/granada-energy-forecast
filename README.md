granada_smart_city/
│
├── .env                    # TUS CLAVES DE SUPABASE (No subir a GitHub)
├── requirements.txt        # Librerías (pandas, fastapi, sqlalchemy, psycopg2-binary, scikit-learn)
├── README.md               # Explicación del proyecto
│
├── data/                   # ALMACÉN DE DATOS (Local)
│   ├── raw/                # Aquí pones el "consumo_granada.csv" original
│   ├── processed/          # (Opcional) Si quieres guardar CSVs limpios intermedios
│   └── models/             # Aquí se guardará tu "modelo_final.joblib"
│
├── notebooks/              # TU LABORATORIO (Data Science)
│   ├── 01_limpieza_analisis.ipynb   # Pruebas de limpieza
│   └── 02_entrenamiento.ipynb       # Pruebas de modelos
│
├── scripts/                # SCRIPTS DE MANTENIMIENTO (Se ejecutan 1 vez)
│   └── ingest_data.py      # EL SCRIPT QUE USA PANDAS PARA SUBIR DATOS A SUPABASE
│
└── src/                    # LA APLICACIÓN WEB (Production Ready)
    ├── __init__.py
    ├── main.py             # Punto de entrada de FastAPI
    ├── config.py           # Configuración (carga el .env)
    ├── database.py         # Conexión a Supabase para la App
    │
    ├── routes/             # Las URLs de tu web
    │   ├── dashboard.py    # Rutas para gráficas
    │   └── prediction.py   # Rutas para predecir
    │
    ├── services/           # Lógica de negocio
    │   └── model_loader.py # Carga el modelo .joblib
    │
    └── templates/          # Tus HTMLs
        ├── base.html
        └── dashboard.html


# ⚡ Granada Smart City: Energy Forecast System

> **Sistema Inteligente de Predicción de Demanda Energética** desarrollado para el Ayuntamiento de Granada.

![Status](https://img.shields.io/badge/Status-Production%20Ready-success)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![AI](https://img.shields.io/badge/Model-Gradient%20Boosting-orange)

## 🎯 Descripción del Proyecto

Este proyecto aborda el desafío de **anticipar la demanda eléctrica** en los distintos barrios de Granada. Hemos transformado datos históricos de sensores (2015-2025) en una aplicación web capaz de realizar **auditorías históricas** y **simulaciones futuras** mediante Inteligencia Artificial.

El sistema no solo predice, sino que es capaz de detectar si se está consultando una fecha futura (sin datos reales) y conmutar automáticamente a un **modo de simulación pura**, estimando la temperatura climática mediante APIs externas.

## 🏗️ Arquitectura Técnica

El proyecto sigue una arquitectura moderna desacoplada:

* **Cerebro (AI):** Modelo `GradientBoostingRegressor` entrenado con métricas cíclicas temporales (Sen/Cos) y One-Hot Encoding.
    * *MAE:* ~139 kWh (Objetivo inicial: <218 kWh).
    * *R² Score:* 0.98.
* **Backend:** `FastAPI` (Python) para la gestión de endpoints asíncronos.
* **Datos:** `Supabase` (PostgreSQL) en la nube para persistencia histórica.
* **Frontend:** `Jinja2` + `Bootstrap 5` + `Chart.js` para visualización interactiva.

## 🚀 Características Clave

### 1. Dashboard Estratégico
Visualización en tiempo real de los KPIs de la ciudad (Consumo medio, picos máximos) y ranking de barrios.

### 2. Auditoría Inteligente (Realidad vs IA)
Comparativa gráfica entre el consumo real registrado y la predicción del modelo. Permite validar la precisión de la IA en fechas pasadas.

### 3. Modo "Viaje al Futuro" 🚀
Si el usuario consulta una fecha futura, el sistema:
1.  Detecta la ausencia de datos reales en Supabase.
2.  Consulta la previsión climática (Open-Meteo).
3.  Genera una predicción puramente sintética.
4.  Informa visualmente al usuario de que está en "Modo Simulación".

## 🛠️ Instalación y Uso

1. **Clonar el repositorio:**
   ```bash
   git clone [https://github.com/tu-usuario/granada-energy-forecast.git](https://github.com/tu-usuario/granada-energy-forecast.git)
   cd granada-energy-forecast