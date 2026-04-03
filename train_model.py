import json
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB

INTENT_FILE = "intents.json"
MODEL_FILE = "model.pkl"
VEC_FILE = "vectorizer.pkl"

def train():
    # Load intents
    with open(INTENT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    sentences = []
    labels = []

    for intent in data["intents"]:
        for pattern in intent["patterns"]:
            sentences.append(pattern)
            labels.append(intent["tag"])

    # Create TF-IDF vectorizer
    vectorizer = TfidfVectorizer(stop_words="english")
    X = vectorizer.fit_transform(sentences)

    # Train Naive Bayes model
    model = MultinomialNB()
    model.fit(X, labels)

    # Save model and vectorizer
    pickle.dump(model, open(MODEL_FILE, "wb"))
    pickle.dump(vectorizer, open(VEC_FILE, "wb"))

    print("✅ Training complete! Model and vectorizer saved.")

if __name__ == "__main__":
    train()
