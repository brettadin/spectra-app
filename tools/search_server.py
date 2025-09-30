import json, pathlib
import faiss, numpy as np
from sentence_transformers import SentenceTransformer
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
import uvicorn

ROOT = pathlib.Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs" / ".index"

app = FastAPI()
model = SentenceTransformer("all-MiniLM-L6-v2")
index = faiss.read_index(str(DOCS / "docs.faiss"))
metas = json.loads((DOCS / "metas.json").read_text(encoding="utf-8"))

@app.get("/search")
def search(q: str = Query(...), k: int = 8, lib: str | None = None):
    qemb = model.encode([q], normalize_embeddings=True)
    sims, ids = index.search(qemb, k)
    results = []
    for score, idx in zip(sims[0], ids[0]):
        m = metas[int(idx)]
        if lib and m.get("lib") != lib:
            continue
        results.append({"score": float(score), **m})
    return JSONResponse(results[:k])

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8765)
