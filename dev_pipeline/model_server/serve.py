import subprocess
import os
import logging
from dotenv import load_dotenv
import mlflow

load_dotenv()

log_dir = "/app/logs"
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "model_serving.log")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_file, encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

MLFLOW_PORT = os.getenv("MLFLOW_PORT", "5000")
MODEL_API_PORT = os.getenv("MLFLOW_API_PORT", "5001")
MODEL_NAME = "NewsSentiment"
MODEL_VERSION = 1

mlflow.set_tracking_uri(f"http://mlflow-tracking:{MLFLOW_PORT}")
logger.info(f"Tracking URI set to: http://mlflow-tracking:{MLFLOW_PORT}")


def serve_model():
    logger.info(
        f"Serving model {MODEL_NAME} version {MODEL_VERSION} on port {MODEL_API_PORT}")
    env = os.environ.copy()
    env["PYTHONPATH"] = os.getcwd()
    try:
        subprocess.run([
            "mlflow", "models", "serve",
            "--model-uri", f"models:/{MODEL_NAME}/{MODEL_VERSION}",
            "--host", "0.0.0.0",
            "--port", MODEL_API_PORT,
            "--no-conda"
        ], env=env, check=True)
        logger.info("Successfully exposed API!")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to serve model: {e}")


if __name__ == "__main__":
    serve_model()
