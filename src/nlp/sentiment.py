import os
import pandas as pd
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
from tqdm import tqdm

def load_mapped():
    path = "data/processed/news_all_mapped.csv"

    if not os.path.exists(path):
        raise SystemExit(
            "Mapped file not found. Run: python -m src.scrape.map_tickers"
        )

    df = pd.read_csv(path)
    if df.empty:
        raise SystemExit("Mapped file is empty. Not enough news yet.")

    return path, df

def load_model():
    tokenizer = AutoTokenizer.from_pretrained("ProsusAI/finbert")
    model = AutoModelForSequenceClassification.from_pretrained("ProsusAI/finbert")
    model.eval()
    return tokenizer, model

@torch.no_grad()
def score_texts(texts, tokenizer, model, batch_size=16, max_length=256):
    scores = []
    confs = []

    for i in tqdm(range(0, len(texts), batch_size)):
        batch = texts[i:i+batch_size]
        enc = tokenizer(batch, padding=True, truncation=True, max_length=max_length, return_tensors="pt")
        logits = model(**enc).logits
        probs = torch.softmax(logits, dim=1)

        # For this FinBERT: [negative, neutral, positive]
        neg = probs[:, 0].cpu().numpy()
        pos = probs[:, 2].cpu().numpy()

        score = pos - neg
        conf = probs.max(dim=1).values.cpu().numpy()

        scores.extend(score.tolist())
        confs.extend(conf.tolist())

    return scores, confs

def main():
    path, df = load_mapped()
    tokenizer, model = load_model()

    texts = (df["title"].fillna("") + " " + df["summary"].fillna("") + " " + df["text"].fillna("")).tolist()
    scores, confs = score_texts(texts, tokenizer, model)

    out = df.copy()
    out["sentiment_score"] = scores
    out["sentiment_confidence"] = confs

    out_path = path.replace("_mapped.csv", "_sentiment.csv")
    out.to_csv(out_path, index=False)
    print(f"Saved -> {out_path}")

if __name__ == "__main__":
    main()
