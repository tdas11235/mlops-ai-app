FROM python:3.9-slim

WORKDIR /app

RUN pip install torch transformers scikit-learn mlflow python-dotenv datasets

RUN mkdir -p /app/mlruns /app/mlartifacts /app/artifacts

COPY launcher.py /app/

EXPOSE 5000

CMD ["python", "launcher.py"]