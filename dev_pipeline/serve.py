import subprocess
import os
from dotenv import load_dotenv
import mlflow


load_dotenv()

MLFLOW_PORT = os.getenv("MLFLOW_PORT", "5000")
MODEL_API_PORT = os.getenv("MLFLOW_API_PORT", "5001")
MODEL_NAME = "NewsSentiment"
MODEL_VERSION = 1
mlflow.set_tracking_uri(f"http://localhost:{MLFLOW_PORT}")
print(f"Tracking URI set to: http://localhost:{MLFLOW_PORT}")


def serve_model():
    print(
        f"Serving model {MODEL_NAME} version {MODEL_VERSION} on port {MODEL_API_PORT}")
    env = os.environ.copy()
    env["PYTHONPATH"] = os.getcwd()
    subprocess.run([
        "mlflow", "models", "serve",
        "--model-uri", f"models:/{MODEL_NAME}/{MODEL_VERSION}",
        "--host", "0.0.0.0",
        "--port", MODEL_API_PORT,
        "--no-conda"
    ], env=env)
    print("Successfully expose API!")


if __name__ == "__main__":
    serve_model()
