import mlflow.pyfunc
import torch
from transformers import AutoTokenizer
from includes.model import TinyBERTClassifier


class SentimentModelWrapper(mlflow.pyfunc.PythonModel):
    def load_context(self, context):
        self.device = torch.device("cpu")
        self.tokenizer = AutoTokenizer.from_pretrained("prajjwal1/bert-tiny")
        self.model = TinyBERTClassifier()
        self.model.load_state_dict(torch.load(
            context.artifacts["model_path"], map_location=self.device))
        self.model.eval()

    def predict(self, context, model_input):
        texts = model_input["text"][0].tolist()
        print(texts)
        encodings = self.tokenizer(
            texts,
            padding="max_length",
            truncation=True,
            max_length=32,
            return_tensors="pt"
        )
        with torch.no_grad():
            logits = self.model(
                encodings["input_ids"], encodings["attention_mask"])
            preds = torch.argmax(logits, dim=1)
        return preds.numpy()
