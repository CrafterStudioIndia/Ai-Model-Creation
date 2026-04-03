import json, random, os

# 📁 Output file
INTENTS_FILE = "intents.json"

# 🎯 Topics — tech, military, science, etc.
TOPICS = [
    "Quantum computing", "Artificial intelligence", "Neural networks", "Blockchain",
    "Augmented reality", "5G technology", "Semiconductors", "NVIDIA GPU",
    "Python programming", "F-35 fighter jet", "AMCA India", "Stealth technology",
    "Aircraft carrier", "Hypersonic missile", "DRDO", "INS Vikramaditya",
    "Apache helicopter", "Arjun tank", "Black hole", "DNA replication",
    "Photosynthesis", "Nuclear fusion", "CRISPR", "String theory",
    "Quantum entanglement", "Mars exploration"
]

# 🧠 Base patterns
PATTERNS = [
    "What is {topic}?",
    "Explain {topic}",
    "Tell me about {topic}",
    "Give me details on {topic}",
    "How does {topic} work?",
    "What's special about {topic}?",
    "Recent news about {topic}",
    "Applications of {topic}",
    "Advantages of {topic}",
    "History of {topic}"
]

# 💬 Generic responses (AI can expand later)
RESPONSES = [
    "{topic} is an advanced field with many real-world applications.",
    "{topic} plays a key role in modern technology and defense.",
    "{topic} combines innovation, science, and engineering excellence.",
    "Research in {topic} is ongoing, with great future potential."
]

# 🔢 You can set this higher (1000000 for 1M intents)
NUM_INTENTS = 1000000

def generate_intents():
    intents = {"intents": []}

    for topic in TOPICS:
        print(f"🧩 Generating intent for: {topic}")
        tag = topic.lower().replace(" ", "_")
        patterns = [p.format(topic=topic) for p in PATTERNS]
        responses = [r.format(topic=topic) for r in RESPONSES]
        intents["intents"].append({
            "tag": tag,
            "patterns": patterns,
            "responses": responses
        })

    # 🧠 Expand to large dataset (duplicates with variation)
    base = intents["intents"].copy()
    for _ in range(NUM_INTENTS // len(TOPICS)):
        for intent in base:
            if len(intents["intents"]) >= NUM_INTENTS:
                break
            i_copy = {
                "tag": intent["tag"],
                "patterns": [p + random.choice(["", " please", " now", " quickly"]) for p in intent["patterns"]],
                "responses": intent["responses"]
            }
            intents["intents"].append(i_copy)

    # 💾 Save safely
    with open(INTENTS_FILE, "w", encoding="utf-8") as f:
        json.dump(intents, f, indent=2, ensure_ascii=False)
    print(f"\n✅ Generated {len(intents['intents'])} intents and saved to {INTENTS_FILE}")

if __name__ == "__main__":
    generate_intents()
