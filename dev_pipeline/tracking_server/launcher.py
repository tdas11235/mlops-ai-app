import subprocess
import os
from dotenv import load_dotenv


load_dotenv()

current_dir = os.getcwd()

MLFLOW_PORT = os.getenv("MLFLOW_PORT", "5000")
MLFLOW_DIR = os.getenv("MLFLOW_DIR", "mlruns")

# Launch MLflow UI
print(f"Starting MLflow UI at http://0.0.0.0:{MLFLOW_PORT}")
subprocess.run([
    "mlflow", "ui",
    "--backend-store-uri", MLFLOW_DIR,
    "--port", MLFLOW_PORT,
    "--host", "0.0.0.0"
])