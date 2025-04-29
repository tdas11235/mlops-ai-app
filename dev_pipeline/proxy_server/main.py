from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import requests
import time

app = FastAPI()

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
        response = requests.post(MLFLOW_INVOCATION_URL, json=input_data)
        response.raise_for_status()
        return Response(content=response.content, media_type=response.headers.get('Content-Type'))
    except Exception as e:
        REQUEST_ERRORS.inc()
        return JSONResponse(status_code=500, content={"error": str(e)})
    finally:
        REQUEST_LATENCY.observe(time.time() - start_time)


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/healthz")
def health():
    return {"status": "ok"}
