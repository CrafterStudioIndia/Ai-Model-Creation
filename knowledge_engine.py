import json
import os
import wikipedia
import requests
from bs4 import BeautifulSoup

KNOWLEDGE_FILE = "knowledge.json"

# ---------------------------- #
# ❗AUTO-LOADING KNOWLEDGE
# ---------------------------- #

def save_knowledge(query, answer):
    if not os.path.exists(KNOWLEDGE_FILE):
        data = {"knowledge": []}
    else:
        with open(KNOWLEDGE_FILE, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except:
                data = {"knowledge": []}

    data["knowledge"].append({"query": query, "answer": answer})

    with open(KNOWLEDGE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    print(f"🧠 Learned: {query}")


def load_local_knowledge(query):
    if not os.path.exists(KNOWLEDGE_FILE):
        return None

    with open(KNOWLEDGE_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    for item in data.get("knowledge", []):
        if item["query"].lower() == query.lower():
            return item["answer"]

    return None


# ---------------------------- #
# 🌐 INTERNET KNOWLEDGE SOURCES
# ---------------------------- #

def get_from_wikipedia(query):
    try:
        summary = wikipedia.summary(query, sentences=3, auto_suggest=True)
        return f"📘 Wikipedia: {summary}"
    except:
        return None


def get_from_duckduckgo(query):
    try:
        url = f"https://api.duckduckgo.com/?q={query}&format=json&no_html=1"
        res = requests.get(url).json()
        if "Abstract" in res and res["Abstract"] != "":
            return f"🦆 DuckDuckGo: {res['Abstract']}"
        return None
    except:
        return None


def scrape_google_fallback(query):
    """
    This does NOT scrape Google search results.
    It only loads a page after selecting a URL from DuckDuckGo.
    So it is legal + safe.
    """
    try:
        results = requests.get(
            f"https://duckduckgo.com/html/?q={query}",
            headers={"User-Agent": "Mozilla/5.0"}
        ).text

        soup = BeautifulSoup(results, "html.parser")
        links = soup.find_all("a", {"class": "result__a"})

        if not links:
            return None

        url = links[0].get("href")

        page = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}).text
        soup2 = BeautifulSoup(page, "html.parser")

        text = " ".join([p.text for p in soup2.find_all("p")][:4])
        if len(text) < 50:
            return None

        return f"🌐 Web Summary: {text[:600]}..."

    except:
        return None


# ---------------------------- #
# 🧠 MASTER FUNCTION
# ---------------------------- #

def get_knowledge(query):
    # 1️⃣ Check local knowledge
    local = load_local_knowledge(query)
    if local:
        return local

    # 2️⃣ Wikipedia
    wiki = get_from_wikipedia(query)
    if wiki:
        save_knowledge(query, wiki)
        return wiki

    # 3️⃣ DuckDuckGo Instant Answer
    ddg = get_from_duckduckgo(query)
    if ddg:
        save_knowledge(query, ddg)
        return ddg

    # 4️⃣ Web Fallback Scraper
    web = scrape_google_fallback(query)
    if web:
        save_knowledge(query, web)
        return web

    # 5️⃣ Nothing found
    return "❌ I could not find any reliable info online."

