from typing import List, Optional
from pydantic import BaseModel


class DocumentCreate(BaseModel):
    title: str
    path: str
    metadata: Optional[dict] = None


class DocumentRead(BaseModel):
    id: int
    tenant_id: int
    title: str
    path: str

    class Config:
        from_attributes = True


class QueryRequest(BaseModel):
    query: str
    top_k: int = 3
    use_web: bool = False


class SourceItem(BaseModel):
    content: str
    source: str
    score: Optional[float] = None


class QueryResponse(BaseModel):
    answer: str
    sources: List[SourceItem]
    metrics: Optional[dict] = None
