from datasets import load_dataset

# Load the Sentiment140 dataset
sentiment140_dataset = load_dataset("stanfordnlp/sentiment140", trust_remote_code=True)

# Load the Financial PhraseBank dataset
financial_phrasebank_dataset = load_dataset(
    "takala/financial_phrasebank", "sentences_50agree", trust_remote_code=True)
print(sentiment140_dataset["train"][:2])
print(financial_phrasebank_dataset["train"][:2])

unique_sentiment140_labels = set(sentiment140_dataset["train"]["sentiment"])
print("Sentiment140 Unique Labels:", unique_sentiment140_labels)

unique_phrasebank_labels = set(financial_phrasebank_dataset["train"]["label"])
print("Financial PhraseBank Unique Labels:", unique_phrasebank_labels)
