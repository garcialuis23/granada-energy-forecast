import pandas as pd
import numpy as np
import joblib
import os
import time
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# --- CONFIGURACIÓN ---
CSV_PATH = "data/processed/consumo_granada_modelo.csv"
MODEL_DIR = "data/models"
MODEL_NAME = "gradient_boosting_model.joblib"
MODEL_PATH = os.path.join(MODEL_DIR, MODEL_NAME)

def train_production_model():
    print("🧠 INICIANDO ENTRENAMIENTO DEL MODELO 'TOP'...")
    start_time = time.time()

    # 1. Cargar datos
    if not os.path.exists(CSV_PATH):
        print(f"❌ Error: No encuentro el archivo {CSV_PATH}")
        return

    print("📂 Cargando dataset procesado...")
    df = pd.read_csv(CSV_PATH)

    # 2. Separar Features (X) y Target (y)
    # Eliminamos columnas que no entran al modelo matemático
    cols_to_drop = ['timestamp', 'consumption_kwh', 'zone_name'] 
    
    # Filtrar solo columnas que existen en el DF
    cols_to_drop = [c for c in cols_to_drop if c in df.columns]

    X = df.drop(columns=cols_to_drop)
    y = df['consumption_kwh']

    print(f"📊 Dimensiones de entrenamiento: {X.shape}")
    print(f"   Features ({len(X.columns)}): {list(X.columns)[:5]} ...")

    # 3. Split Train/Test (80% - 20%)
    # Usamos random_state=42 para que siempre salga el mismo resultado (reproducibilidad)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # 4. Configuración del Modelo (Hiperparámetros del Notebook)
    # Estos valores suelen dar el mejor equilibrio para este tipo de datos
    gb_model = GradientBoostingRegressor(
        n_estimators=300,       # Número de árboles (Potencia)
        learning_rate=0.1,      # Velocidad de aprendizaje
        max_depth=5,            # Profundidad (Complejidad)
        min_samples_split=10,   # Evitar overfitting
        min_samples_leaf=5,     # Evitar overfitting
        random_state=42,
        verbose=1               # Muestra progreso
    )

    # 5. Entrenamiento
    print("\n🔥 Entrenando Gradient Boosting (Paciencia, busca la mejor precisión)...")
    gb_model.fit(X_train, y_train)

    # 6. Evaluación
    print("\n🧐 Evaluando rendimiento...")
    predictions = gb_model.predict(X_test)

    mae = mean_absolute_error(y_test, predictions)
    rmse = np.sqrt(mean_squared_error(y_test, predictions))
    r2 = r2_score(y_test, predictions)

    print("\n" + "="*50)
    print(f"🏆 RESULTADOS DEL MODELO FINAL")
    print("="*50)
    print(f"Error Medio Absoluto (MAE):   {mae:.2f} kWh")
    print(f"Raíz Error Cuadrático (RMSE): {rmse:.2f} kWh")
    print(f"Precisión (R² Score):         {r2:.4f}")
    print("-" * 50)

    # 7. Verificación de Calidad
    if mae < 250:
        print("✅ CALIDAD: EXCELENTE. El modelo está listo para producción.")
    elif mae < 450:
        print("⚠️ CALIDAD: ACEPTABLE. Puede mejorarse.")
    else:
        print("❌ CALIDAD: BAJA. Algo ha fallado en los datos.")

    # 8. Guardar Modelo
    if not os.path.exists(MODEL_DIR):
        os.makedirs(MODEL_DIR)

    joblib.dump(gb_model, MODEL_PATH)
    
    elapsed = time.time() - start_time
    print(f"\n💾 Modelo guardado en: {MODEL_PATH}")
    print(f"⏱️ Tiempo total: {elapsed:.2f} segundos")

if __name__ == "__main__":
    train_production_model()    