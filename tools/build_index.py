import json, pathlib
import faiss, numpy as np
from sentence_transformers import SentenceTransformer

ROOT = pathlib.Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
MIR = DOCS / "mirrored"
IDX = DOCS / ".index"
IDX.mkdir(parents=True, exist_ok=True)

def yield_chunks(text, meta, max_words=900, overlap=120):
    paras = [p.strip() for p in text.split("\n\n") if p.strip()]
    buf, count = [], 0
    for p in paras:
        w = len(p.split())
        if count + w > max_words and buf:
            joined = "\n\n".join(buf)
            yield joined, meta
            carry = " ".join(joined.split()[-overlap:])
            buf, count = [carry, p], len(carry.split()) + w
        else:
            buf.append(p); count += w
    if buf:
        yield "\n\n".join(buf), meta

def build(model_name="all-MiniLM-L6-v2"):
    texts, metas = [], []
    for md_file in MIR.rglob("*.md"):
        md = md_file.read_text(encoding="utf-8")
        meta = json.loads(md_file.with_suffix(".meta.json").read_text(encoding="utf-8"))
        lib = md_file.relative_to(MIR).parts[0]
        meta.update({"lib": lib, "path": str(md_file.relative_to(MIR))})
        for chunk, m in yield_chunks(md, meta):
            texts.append(chunk); metas.append(m)
    model = SentenceTransformer(model_name)
    embs = model.encode(texts, convert_to_numpy=True, show_progress_bar=True, normalize_embeddings=True)
    index = faiss.IndexFlatIP(embs.shape[1])
    index.add(embs)
    faiss.write_index(index, str(IDX / "docs.faiss"))
    (IDX / "metas.json").write_text(json.dumps(metas), encoding="utf-8")
    print(f"[indexed] {len(texts)} chunks")

if __name__ == "__main__":
    build()
