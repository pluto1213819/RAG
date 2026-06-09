import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, ".")

from pathlib import Path
from rag_core.vector_store import ingest_texts
from app.db import SessionLocal, Base, engine
from app.models import Document

Base.metadata.create_all(bind=engine)
db = SessionLocal()

templates = Path("templates")
files = sorted(templates.glob("*.md"))
total_chunks = 0

for f in files:
    text = f.read_text(encoding="utf-8")
    chunks = [p.strip() for p in text.split("\n\n") if p.strip()]

    doc = db.query(Document).filter(Document.title == f.stem).first()
    if not doc:
        doc = Document(title=f.stem, path=str(f), metadata_={"kind": "knowledge"})
        db.add(doc)
        db.commit()
        doc = db.query(Document).filter(Document.title == f.stem).first()

    ingest_texts(doc.id, chunks, metadata={"title": f.stem, "path": str(f)})
    total_chunks += len(chunks)
    print("  Indexed: %s -> %d chunks" % (f.name, len(chunks)))

db.close()
print("\nDone! Indexed %d files, %d chunks total." % (len(files), total_chunks))
