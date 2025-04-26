FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y curl

RUN pip install torch transformers scikit-learn mlflow python-dotenv datasets

COPY . /app/

EXPOSE 5001