import torch
from transformers import AutoTokenizer
from torch.utils.data import DataLoader
import torch.nn as nn
import torch.optim as optim
import mlflow
from model import TinyBERTClassifier
from data_loader import GetDataset
from build_data import load_combined
import os
from sklearn.metrics import accuracy_score
from inference_wrapper import SentimentModelWrapper
import datetime


device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
EPOCHS = 5


mlflow_tracking_uri = f"http://127.0.0.1:5000"
mlflow.set_tracking_uri(mlflow_tracking_uri)
mlflow.set_experiment("SentimentNewsClassifier")

def train():
    run_name = "fintune"
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    run_name = f"{run_name}_{timestamp}"
    with mlflow.start_run(run_name=run_name) as run:
        try:
            texts, labels = load_combined(random_state=42)
            tokenizer = AutoTokenizer.from_pretrained("prajjwal1/bert-tiny")
            dataset = GetDataset(texts, labels, tokenizer)
            loader = DataLoader(dataset, batch_size=16, shuffle=True)
            model = TinyBERTClassifier()
            model.train()
            criterion = nn.CrossEntropyLoss()
            optimizer = optim.Adam(model.classifier.parameters(), lr=5e-4)
            for epoch in range(EPOCHS):
                total_loss = 0
                all_preds = []
                all_labels = []
                for batch in loader:
                    optimizer.zero_grad()
                    input_ids = batch["input_ids"]
                    attention_mask = batch["attention_mask"]
                    labels = batch["labels"]
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
                print(f"Epoch {epoch+1} Loss: {total_loss:.4f}, Accuracy: {acc:.4f}")

            artifacts_dir = "artifacts"
            os.makedirs(artifacts_dir, exist_ok=True)
            model_path = os.path.join(artifacts_dir, "tinybert.pt")
            torch.save(model.state_dict(), model_path)
            mlflow.log_param("epochs", EPOCHS)
            mlflow.log_param("model_name", "prajjwal1/bert-tiny")
            mlflow.pyfunc.log_model(
                artifact_path="sentiment_model",
                python_model=SentimentModelWrapper(),
                artifacts={"model_path": model_path}
            )
            mlflow.register_model(f"runs:/{run.info.run_id}/sentiment_model", "NewsSentiment")
        except Exception as e:
            mlflow.log_param("error", str(e))
            print(f"Training failed due to: {e}")
            raise


if __name__ == "__main__":
    train()