import torch
from transformers import AutoTokenizer
from torch.utils.data import DataLoader
import torch.nn as nn
import torch.optim as optim
import mlflow
import mlflow.pyfunc
from mlflow.tracking import MlflowClient
from includes.model import TinyBERTClassifier
from includes.data_loader import GetDataset
from includes.build_data import load_csv
from includes.inference_wrapper import SentimentModelWrapper
import os
import datetime
import tempfile
from sklearn.metrics import accuracy_score

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
EPOCHS = 5

mlflow_tracking_uri = "http://mlflow-tracking:5000"
mlflow.set_tracking_uri(mlflow_tracking_uri)
mlflow.set_experiment("SentimentNewsClassifier")


def train(csv_path):
    run_name = f"finetune_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    model_name = "NewsSentiment"

    with mlflow.start_run(run_name=run_name) as run:
        try:
            # Load dataset
            texts, labels = load_csv(csv_path)
            tokenizer = AutoTokenizer.from_pretrained("prajjwal1/bert-tiny")
            dataset = GetDataset(texts, labels, tokenizer)
            loader = DataLoader(dataset, batch_size=16, shuffle=True)

            # Init model
            model = TinyBERTClassifier()
            model.to(device)

            # Load latest model weights if available
            client = MlflowClient()
            try:
                versions = client.search_model_versions(f"name='{model_name}'")
                if versions:
                    latest_version = max(
                        versions, key=lambda x: int(x.version))
                    model_uri = latest_version.source
                    print(
                        f"Loading weights from latest version: v{latest_version.version}")
                    loaded_model = mlflow.pytorch.load_model(
                        model_uri=model_uri, map_location=device)
                    model.load_state_dict(loaded_model.state_dict())
                    print("Loaded weights from latest model.")
                    mlflow.log_param("loaded_model_version",
                                     latest_version.version)
                else:
                    print("No registered model versions found. Training from scratch.")
            except Exception as e:
                print(f"Could not load latest model version: {e}")

            model.train()
            criterion = nn.CrossEntropyLoss()
            optimizer = optim.Adam(model.classifier.parameters(), lr=5e-4)

            for epoch in range(EPOCHS):
                total_loss = 0
                all_preds = []
                all_labels = []
                for batch in loader:
                    optimizer.zero_grad()
                    input_ids = batch["input_ids"].to(device)
                    attention_mask = batch["attention_mask"].to(device)
                    labels = batch["labels"].to(device)

                    outputs = model(input_ids, attention_mask)
                    loss = criterion(outputs, labels)
                    loss.backward()
                    optimizer.step()

                    total_loss += loss.item()
                    preds = torch.argmax(outputs, dim=1).cpu().numpy()
                    all_preds.extend(preds)
                    all_labels.extend(labels.cpu().numpy())

                acc = accuracy_score(all_labels, all_preds)
                mlflow.log_metric("loss", total_loss, step=epoch)
                mlflow.log_metric("accuracy", acc, step=epoch)
                print(
                    f"Epoch {epoch+1} Loss: {total_loss:.4f}, Accuracy: {acc:.4f}")

            # Save model to temp file for MLflow pyfunc
            with tempfile.TemporaryDirectory() as tmpdir:
                model_path = os.path.join(tmpdir, "tinybert.pt")
                torch.save(model.state_dict(), model_path)

                mlflow.log_param("epochs", EPOCHS)
                mlflow.log_param("model_name", "prajjwal1/bert-tiny")

                mlflow.pyfunc.log_model(
                    artifact_path="sentiment_model",
                    python_model=SentimentModelWrapper(),
                    artifacts={"model_path": model_path}
                )

                # Register the new model version
                mlflow.register_model(
                    f"runs:/{run.info.run_id}/sentiment_model", model_name)

        except Exception as e:
            mlflow.log_param("error", str(e))
            print(f"Training failed due to: {e}")
            raise


if __name__ == "__main__":
    train()
