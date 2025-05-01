from datasets import load_dataset
from sklearn.model_selection import train_test_split
import pandas as pd


def save_to_csv(texts, labels, csv_path="combined_dataset.csv"):
    if len(texts) != len(labels):
        raise ValueError("Lengths of texts and labels must match.")

    df = pd.DataFrame({'text': texts, 'label': labels})
    df.to_csv(csv_path, index=False)
    print(f"Saved dataset with {len(df)} samples to {csv_path}")

def map_sentiment140_label(label):
    return 0 if label == 0 else 2

def load_combined(random_state=42):
    sentiment140 = load_dataset("stanfordnlp/sentiment140", split="train", trust_remote_code=True)
    phrasebank = load_dataset(
        "takala/financial_phrasebank", "sentences_allagree", split="train", trust_remote_code=True)
    texts_140 = [x["text"] for x in sentiment140 if x["sentiment"] in [0, 4]]
    labels_140 = [map_sentiment140_label(
        x["sentiment"]) for x in sentiment140 if x["sentiment"] in [0, 4]]
    # Stratified sample: 2000 total (equal pos/neg)
    texts_140_train, _, labels_140_train, _ = train_test_split(
        texts_140, labels_140, train_size=2000, stratify=labels_140, random_state=random_state
    )
    texts_fin = [x["sentence"] for x in phrasebank]
    labels_fin = [x["label"] for x in phrasebank]
    # Combine all
    texts = texts_140_train + texts_fin
    labels = labels_140_train + labels_fin
    print(f"Final dataset size: {len(texts)} samples")
    print("Label counts:", {i: labels.count(i) for i in set(labels)})
    return texts, labels


if __name__ == "__main__":
    texts, labels = load_combined()
    save_to_csv(texts, labels)