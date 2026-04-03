import json, os, joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB

def retrain():
    with open("intents.json", "r", encoding="utf-8") as f:
        intents = json.load(f)

    if os.path.exists("knowledge_base.json"):
        with open("knowledge_base.json", "r", encoding="utf-8") as f:
            kb = json.load(f)
        for topic, info in kb.items():
            intents["intents"].append({
                "tag": f"knowledge_{topic}",
                "patterns": [f"What is {topic}", f"Tell me about {topic}", topic],
                "responses": [info]
            })

    X, y = [], []
    for intent in intents["intents"]:
        for pattern in intent["patterns"]:
            X.append(pattern)
            y.append(intent["tag"])

    vectorizer = TfidfVectorizer()
    X_vec = vectorizer.fit_transform(X)
    clf = MultinomialNB().fit(X_vec, y)

    os.makedirs("models", exist_ok=True)
    joblib.dump(clf, "models/intent_model.joblib")
    joblib.dump(vectorizer, "models/vectorizer.joblib")

    print("✅ Model retrained with new knowledge")

if __name__ == "__main__":
    retrain()
