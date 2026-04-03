import json, os, re
import wikipedia
from googlesearch import search

KNOWLEDGE_FILE = "knowledge.json"

def clean_text(text):
    text = re.sub(r'\[[0-9]+\]', '', text)
    return ' '.join(text.split())

def search_wikipedia(query):
    try:
        summary = wikipedia.summary(query, sentences=3, auto_suggest=True)
        return clean_text(summary)
    except wikipedia.exceptions.DisambiguationError as e:
        # Take first suggestion if too many results
        option = e.options[0] if e.options else None
        if option:
            try:
                return wikipedia.summary(option, sentences=2)
            except Exception:
                return None
        return None
    except Exception:
        return None

def search_google_snippet(query):
    try:
        results = list(search(query, num_results=2))
        if results:
            return f"I found this on Google: {results[0]}"
    except Exception:
        return None
    return None

def get_knowledge(query):
    # Try local first
    if os.path.exists(KNOWLEDGE_FILE):
        with open(KNOWLEDGE_FILE, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                for item in data.get("knowledge", []):
                    if item["query"].lower() == query.lower():
                        return item["answer"]
            except json.JSONDecodeError:
                # Reset file if corrupted
                data = {"knowledge": []}

    # Otherwise fetch from web
    answer = search_wikipedia(query)
    if not answer:
        answer = search_google_snippet(query)

    if not answer:
        return "Sorry, I couldn’t find any reliable information on that."

    # Save new knowledge
    save_knowledge(query, answer)
    return answer

def save_knowledge(query, answer):
    data = {"knowledge": []}
    if os.path.exists(KNOWLEDGE_FILE):
        try:
            with open(KNOWLEDGE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError:
            data = {"knowledge": []}

    data["knowledge"].append({"query": query, "answer": answer})
    with open(KNOWLEDGE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    print(f"✅ Learned new knowledge: {query}")
