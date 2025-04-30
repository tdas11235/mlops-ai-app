import pandas as pd


def load_csv(csv_path):
    df = pd.read_csv(csv_path, header=None, names=[
                     "article_id", "label", "text", "timestamp"])
    texts = df["text"].tolist()
    labels = df["label"].tolist()
    print(f"Loaded {len(texts)} samples from {csv_path}")
    print("Label counts:", {i: labels.count(i) for i in set(labels)})
    return texts, labels
