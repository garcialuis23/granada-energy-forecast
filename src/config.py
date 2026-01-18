import os
from pathlib import Path
from dotenv import load_dotenv
import urllib.parse

# Cargar variables de entorno
load_dotenv()

# --- RUTAS DE DIRECTORIOS (Manteniendo tu estructura) ---
BASE_DIR = Path(__file__).resolve().parent.parent # Sube desde src/ a raíz
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = DATA_DIR / "models"
STATIC_DIR = BASE_DIR / "src" / "static"
TEMPLATES_DIR = BASE_DIR / "src" / "templates"

# --- RUTA DEL MODELO ---
# Apunta al archivo exacto que generó el script de entrenamiento
MODEL_PATH = MODELS_DIR / "gradient_boosting_model.joblib"

# --- CONFIGURACIÓN BASE DE DATOS (SUPABASE) ---
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "postgres")

# Construcción segura de la URL (Codificando símbolos en la contraseña)
encoded_password = urllib.parse.quote_plus(DB_PASSWORD) if DB_PASSWORD else ""
DATABASE_URL = f"postgresql://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"