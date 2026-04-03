# api_server.py
import os
import json
import traceback
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

# Try to load model with multiple fallbacks
import pickle
import joblib

# Import your auto-knowledge engine (the one that saves to knowledge.json)
# file should be named knowledge_engine.py or knowledge_collector.py
try:
    from knowledge_engine import get_knowledge
except Exception:
    try:
        from knowledge_collector import get_knowledge
    except Exception:
        # fallback that returns a message
        def get_knowledge(q):
            return "Knowledge engine not available."

# Settings
MODEL_FILES_TO_TRY = [
    "model.pkl",
    "models/intent_model.joblib",
    "intent_model.pkl",
    "intent_model.joblib",
    "models/intent_model.joblib",
    "models/intent_model.pkl",
    "models/model.joblib"
]
VEC_FILES_TO_TRY = [
    "vectorizer.pkl",
    "vectorizer.joblib",
    "models/vectorizer.joblib",
    "models/vectorizer.pkl",
    "vectorizer.pkl"
]

INTENTS_FILE = "intents.json"

app = FastAPI(title="Jarvis Tech Assistant — AutoLearning API")

# Allow simple web UI access from anywhere (during dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# mount static and templates if present
if os.path.isdir("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates") if os.path.isdir("templates") else None

# ------------------------
# Load intents (if present)
# ------------------------
intents = []
if os.path.exists(INTENTS_FILE):
    try:
        with open(INTENTS_FILE, "r", encoding="utf-8") as f:
            intents_data = json.load(f)
            intents = intents_data.get("intents", [])
            print(f"Loaded {len(intents)} intents from {INTENTS_FILE}")
    except Exception as e:
        print("Warning: failed to load intents.json:", e)
else:
    print("Warning: intents.json not found. Knowledge engine will handle unknown queries.")

# ------------------------
# Load model & vectorizer
# ------------------------
model = None
vectorizer = None
loaded_model_file = None
loaded_vec_file = None

def try_load_model():
    global model, vectorizer, loaded_model_file, loaded_vec_file
    # try joblib/pickle for each candidate pair
    for mf in MODEL_FILES_TO_TRY:
        if os.path.exists(mf):
            try:
                # try joblib first
                try:
                    model = joblib.load(mf)
                    loaded_model_file = mf
                    print("Loaded model via joblib:", mf)
                    break
                except Exception:
                    model = pickle.load(open(mf, "rb"))
                    loaded_model_file = mf
                    print("Loaded model via pickle:", mf)
                    break
            except Exception as e:
                print(f"Failed loading model {mf}: {e}")
    for vf in VEC_FILES_TO_TRY:
        if os.path.exists(vf):
            try:
                try:
                    vectorizer = joblib.load(vf)
                    loaded_vec_file = vf
                    print("Loaded vectorizer via joblib:", vf)
                    break
                except Exception:
                    vectorizer = pickle.load(open(vf, "rb"))
                    loaded_vec_file = vf
                    print("Loaded vectorizer via pickle:", vf)
                    break
            except Exception as e:
                print(f"Failed loading vectorizer {vf}: {e}")

try_load_model()

if model is None or vectorizer is None:
    print("⚠️ Model or vectorizer not found or failed to load. The server will still run but will rely on the knowledge engine for unknown queries.")
else:
    # If model is a scikit-learn Pipeline, we can use it directly
    print(f"✅ Model ready (model: {loaded_model_file}, vectorizer: {loaded_vec_file})")

# ------------------------
# Helper: find canned response for an intent tag
# ------------------------
def canned_response_for_tag(tag):
    for intent in intents:
        if intent.get("tag") == tag:
            # return first response if list exists
            resp = intent.get("responses")
            if isinstance(resp, list) and resp:
                return resp[0]
            elif isinstance(resp, str):
                return resp
    return None

# ------------------------
# Routes
# ------------------------
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    # if templates exist, render index.html, else return simple JSON
    if templates:
        return templates.TemplateResponse("index.html", {"request": request})
    return JSONResponse({"message": "Jarvis Tech Assistant API is running. No templates/ UI detected."})

@app.post("/ask")
async def ask(request: Request):
    """POST JSON: {"message":"..."} -> returns {"intent":..., "response":...}"""
    try:
        payload = await request.json()
        text = (payload.get("message") or "").strip()
        if not text:
            return JSONResponse({"intent": None, "response": "Please send non-empty message."})

        # 1) If model is available, predict intent
        if model is not None and vectorizer is not None:
            try:
                # model might be pipeline or separate
                # if model is a pipeline, it will accept raw text
                if hasattr(model, "predict") and hasattr(vectorizer, "transform"):
                    # if model expects vectorized input (separate vectorizer), transform
                    X_vec = vectorizer.transform([text])
                    intent = model.predict(X_vec)[0]
                else:
                    # fallback: try model.predict on raw text
                    intent = model.predict([text])[0]
            except Exception:
                # try pipeline style prediction
                try:
                    intent = model.predict([text])[0]
                except Exception:
                    intent = None
        else:
            intent = None

        # 2) Look up canned response
        response = None
        if intent:
            response = canned_response_for_tag(intent)

        # 3) If no canned response or model not confident, use knowledge engine
        if not response:
            # get_knowledge should handle caching and saving automatically
            try:
                response = get_knowledge(text)
            except Exception as e:
                print("Knowledge engine error:", e)
                response = "Sorry — knowledge lookup failed."

        return JSONResponse({"intent": intent, "response": response})
    except Exception as e:
        traceback.print_exc()
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/retrain")
async def retrain():
    """
    Optional endpoint: tries to call a local train script train_model.py (must define train() or be executable)
    Use with caution (heavy).
    """
    try:
        if not os.path.exists("train_model.py"):
            return JSONResponse({"error": "train_model.py not found in project root."}, status_code=400)
        # import train_model dynamically and call train() if available
        import importlib.util
        spec = importlib.util.spec_from_file_location("train_model", os.path.join(os.getcwd(), "train_model.py"))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        if hasattr(module, "train"):
            module.train()
            # reload model after training
            try_load_model()
            return JSONResponse({"status": "retrained", "model_file": loaded_model_file})
        else:
            # if module just runs training when executed, that's acceptable
            return JSONResponse({"status": "train_model.py executed (no train() function found)."}, status_code=200)
    except Exception as e:
        traceback.print_exc()
        return JSONResponse({"error": str(e)}, status_code=500)

# Serve raw knowledge file for inspection
@app.get("/knowledge")
async def knowledge():
    if os.path.exists("knowledge.json"):
        return FileResponse("knowledge.json", media_type="application/json")
    return JSONResponse({"message": "No knowledge.json found yet."}, status_code=404)

# Health
@app.get("/health")
async def health():
    return {
        "status": "ok",
        "model_loaded": model is not None,
        "intents_loaded": len(intents)
    }

# ------------------------
# Run as main for dev convenience
# ------------------------
if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Jarvis API (dev mode)...")
    uvicorn.run("api_server:app", host="127.0.0.1", port=8000, reload=True)
