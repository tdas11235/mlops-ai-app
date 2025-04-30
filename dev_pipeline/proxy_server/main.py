from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import requests
import time
import logging
import os

app = FastAPI()

# Set up logging
log_dir = "/app/logs"
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "api.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_file, encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter("model_requests_total", "Total number of requests")
REQUEST_LATENCY = Histogram(
    "model_request_latency_seconds", "Request latency in seconds")
REQUEST_ERRORS = Counter("model_request_errors_total",
                         "Number of failed requests")

MLFLOW_INVOCATION_URL = "http://mlflow-model:5001/invocations"


@app.post("/predict")
async def predict(request: Request):
    REQUEST_COUNT.inc()
    start_time = time.time()
    try:
        input_data = await request.json()
        logger.info(f"Received prediction request: {input_data}")
        response = requests.post(MLFLOW_INVOCATION_URL, json=input_data)
        response.raise_for_status()
        logger.info("Successfully received response from MLflow model.")
        return Response(content=response.content, media_type=response.headers.get('Content-Type'))
    except Exception as e:
        logger.error(f"Prediction request failed: {e}")
        REQUEST_ERRORS.inc()
        return JSONResponse(status_code=500, content={"error": str(e)})
    finally:
        latency = time.time() - start_time
        REQUEST_LATENCY.observe(latency)
        logger.info(f"Request latency: {latency:.4f} seconds")


@app.get("/metrics")
def metrics():
    logger.debug("Metrics endpoint hit.")
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/healthz")
def health():
    logger.debug("Health check OK.")
    return {"status": "ok"}
