import subprocess
import os
import logging
from dotenv import load_dotenv

load_dotenv()

# Setup logging
log_dir = "/app/logs"
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "mlflow_ui.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_file, encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

MLFLOW_PORT = os.getenv("MLFLOW_PORT", "5000")
MLFLOW_DIR = os.getenv("MLFLOW_DIR", "mlruns")

# Launch MLflow UI
logger.info(f"Starting MLflow UI at http://0.0.0.0:{MLFLOW_PORT}")

try:
    subprocess.run([
        "mlflow", "ui",
        "--backend-store-uri", MLFLOW_DIR,
        "--port", MLFLOW_PORT,
        "--host", "0.0.0.0"
    ], check=True)
except subprocess.CalledProcessError as e:
    logger.error(f"Failed to start MLflow UI: {e}")
