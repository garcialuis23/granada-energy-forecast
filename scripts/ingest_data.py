import pandas as pd
import os
from sqlalchemy import create_engine
from dotenv import load_dotenv
import urllib.parse 

load_dotenv()

def ingest_optimized_data():
    # --- CONFIGURACIÓN ---
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", "postgres")

    encoded_password = urllib.parse.quote_plus(DB_PASSWORD)
    DATABASE_URL = f"postgresql://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    CSV_PATH = "data/processed/consumo_granada_modelo.csv"
    
    if not os.path.exists(CSV_PATH):
        print(f"❌ Error: No encuentro {CSV_PATH}")
        return

    print("🚀 Cargando CSV (Versión Optimizada)...")
    df = pd.read_csv(CSV_PATH)
    
    # --- PASO 1: RECONSTRUIR ZONE_NAME ---
    print("🔄 Reconstruyendo nombre de zona...")
    df.columns = df.columns.str.lower()
    zone_cols = [col for col in df.columns if col.startswith('zona_')]
    
    # Creamos la columna bonita
    df['zone_name'] = df[zone_cols].idxmax(axis=1).str.replace('zona_', '').str.replace('_', ' ').str.title()
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    # --- PASO 2: LA DIETA (SELECCIONAR SOLO LO ÚTIL) ---
    # Para el Dashboard solo necesitamos esto. 
    # Las columnas matemáticas (sin/cos/one-hot) las calcula el modelo al vuelo.
    columnas_a_guardar = [
        'timestamp', 
        'zone_name', 
        'consumption_kwh', 
        'temperature',
        'hour', 
        'month', 
        'year', 
        'day_of_week', 
        'is_holiday' # Esta sí es útil para filtrar en gráficas
    ]
    
    df_light = df[columnas_a_guardar].copy()
    
    print(f"📉 Reducción de columnas: De {len(df.columns)} a {len(df_light.columns)}")
    print(f"📊 Ejemplo final ({len(df_light)} filas):")
    print(df_light.head(3))
    
    # --- PASO 3: SUBIR VERSIÓN LIGHT ---
    try:
        print("☁️ Conectando a Supabase...")
        engine = create_engine(DATABASE_URL)
        
        print("📤 Subiendo tabla optimizada...")
        # Usamos chunksize más grande porque ahora pesan menos las filas
        df_light.to_sql('consumo_granada', engine, if_exists='replace', index=False, chunksize=5000)
        
        print("\n🎉 ¡ÉXITO! Datos subidos. Deberían ocupar aprox 150-200MB.")
        
    except Exception as e:
        print(f"\n❌ Error en la subida:\n{e}")

if __name__ == "__main__":
    ingest_optimized_data()