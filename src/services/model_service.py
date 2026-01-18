import joblib
import pandas as pd
import numpy as np
from src.config import MODEL_PATH

class ModelService:
    def __init__(self):
        self.model = None
        self.feature_names = None
        self.load_model()

    def load_model(self):
        try:
            print(f"🧠 Cargando modelo desde {MODEL_PATH}...")
            self.model = joblib.load(MODEL_PATH)
            # Intentar obtener nombres de features del modelo
            if hasattr(self.model, "feature_names_in_"):
                self.feature_names = self.model.feature_names_in_
            else:
                self.feature_names = [] # Fallback
            print("✅ Modelo cargado en memoria.")
        except Exception as e:
            print(f"❌ Error fatal cargando modelo: {e}")

    def predict(self, date_str: str, zone_name: str, temperature: float):
        if not self.model:
            return None

        # 1. Procesar Fecha
        dt = pd.to_datetime(date_str)
        
        # 2. Reconstruir Features Matemáticas (Idéntico al notebook)
        # Esto es lo que hace "inteligente" al sistema
        hour = dt.hour
        month = dt.month
        day_of_week = dt.dayofweek
        
        # Diccionario base con todas las columnas a 0
        input_data = {col: 0 for col in self.feature_names}
        
        # Llenar datos numéricos
        input_data.update({
            'temperature': temperature,
            'hour': hour,
            'month': month,
            'day_of_month': dt.day,
            'day_of_week': day_of_week,
            'year': dt.year,
            'hour_sin': np.sin(2 * np.pi * hour / 24),
            'hour_cos': np.cos(2 * np.pi * hour / 24),
            'month_sin': np.sin(2 * np.pi * month / 12),
            'month_cos': np.cos(2 * np.pi * month / 12),
            'temp_sq': temperature ** 2,
            'is_weekend': 1 if day_of_week >= 5 else 0,
            'is_holiday': 1 if day_of_week >= 5 else 0, # Simplificado
            'is_non_working': 1 if day_of_week >= 5 else 0
        })
        
        # Llenar Zona (One-Hot)
        # Busca la columna "zona_Albaicin_..." y la pone a 1
        target_col_start = f"zona_{zone_name.replace(' ', '_')}"
        for col in self.feature_names:
            if col.lower().startswith(target_col_start.lower()):
                input_data[col] = 1
                break
        
        # Crear DataFrame y Predecir
        df_input = pd.DataFrame([input_data])
        df_input = df_input[self.feature_names] # Asegurar orden
        
        return round(self.model.predict(df_input)[0], 2)

# Instancia única
predictor = ModelService()