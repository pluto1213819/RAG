from app.db import SessionLocal, Base, engine
from app.models import Tenant, User, Document
from app.auth import hash_password


def run():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    tenant = db.query(Tenant).filter(Tenant.name == "demo").first()
    if not tenant:
        tenant = Tenant(name="demo")
        db.add(tenant)
        db.commit()
        db.refresh(tenant)

    owner = db.query(User).filter(User.email == "owner@example.com").first()
    if not owner:
        owner = User(tenant_id=tenant.id, email="owner@example.com", hashed_password=hash_password("owner123"), role="owner")
        db.add(owner)
        db.commit()

    doc = db.query(Document).filter(Document.title == "seed_doc").first()
    if not doc:
        doc = Document(tenant_id=tenant.id, title="seed_doc", path="templates/seed_data.md", metadata_={"kind": "seed"})
        db.add(doc)
        db.commit()

    print("Seed done: tenant=demo, owner=owner@example.com / owner123")


if __name__ == "__main__":
    run()
