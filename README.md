# News Sentiment Analysis

**Name**: Tarak Das
**Roll No.**:  CH21B108

## Code Structure

- `client_runtime/`
    - `backend/`
        - `app.py`: main code for FastAPI
        - `Dockerfile`
        - `logger_config.py`
        - `requirements.txt`
        - `waiter.sh`: bash script to check database readiness
    - `frontend/`
        - `app.py`: Streamlit script for the frontend
        - `Dockerfile`
        - `requirements.txt`
    - `db/`
        - `init.sql`: sets up the user and password for the database
        - `Dockerfile`
    - `rss_reader/`
        - `includes/`
            - `db_utils.py`: script to push data into database
            - `fetcher.py`: fetches RSS feeds and passes on for sentiment analysis
            - `image_utils.py`: script for downloading and base64 encoding images
        - `rss_reader.py`: sets up the worker and scheduler for the whole pipeline
        - `Dockerfile`
        - `logger_config.py`
        - `requirements.txt`
        - `waiter.sh`
    - `logs/`: has service-wise logs for client runtime

- `dev_pipeline/`
    - `airflow_pipeline/`
        - `dags/`
            - `includes/`: helper scripts for DAGs
            - `dag1.py`: DAG for data-ingestion and feedback-retraining
    - `artifacts/`: the base fine-tuned TinyBERT model
    - `model_server/`
        - `logs/`
        - `inference_wrapper.py`: Pyfunc wrapper for inference
        - `model.py`: the BERT-based classifier model
        - `serve.py`: script to serve the registered model based on version
        - `Dockerfile`
    - `proxy_server/`
        - `logs/`
        - `main.py`: FastAPI script to re-route requests to model server and expose metrics
        - `Dockerfile`
        - `requirements.txt`
    - `tracking_server/`
        - `logs/`
        - `Dockerfile`
        - `launcher.py`: spawns the MLflow tracking server

- `prometheus/`
    - `prometheus.yml`: Prometheus configuration for scraping

- `shared_data/`: `feedback.csv` for feedback data

- Environment files:
    - `.client.env`: for client runtime
    - `.env`: for Airflow

- Compose files:
    - `docker-compose.yaml`: for client runtime
    - `docker-compose.dev.yaml`: for dev pipeline
    - `docker-compose.prom.yaml`: for monitoring (Prometheus, Grafana)

- `dashboard.json`: Grafana dashboard

- `node_exporter`

## Executing the code

Set-up the airflow directories
```bash
cd dev_pipeline/airflow_pipeline
mkdir -p logs plugins
```

Build and start the docker containers (for the first time)
```bash
docker compose -f docker-compose.dev.yaml up -d --build && \
docker compose up -d --build && \
docker compose -f docker-compose.prom.yaml up -d --build
```

Start the docker containers
```bash
docker compose -f docker-compose.dev.yaml up -d && \
docker compose up -d && \
docker compose -f docker-compose.prom.yaml up -d
```