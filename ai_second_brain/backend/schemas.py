import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict

class KnowledgeItemBase(BaseModel):
    title: str
    content: str
    type: str = "note" # note, link, idea, task, draft
    url: Optional[str] = None
    category: Optional[str] = "General"
    tags: Optional[str] = ""
    deadline: Optional[str] = None
    priority: Optional[str] = "Medium"
    status: Optional[str] = "Active"

class KnowledgeItemCreate(KnowledgeItemBase):
    pass

class KnowledgeItemUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    type: Optional[str] = None
    url: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[str] = None
    deadline: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None

class KnowledgeItemResponse(KnowledgeItemBase):
    id: int
    extracted_actions: Optional[str] = None
    ai_summary: Optional[str] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

class SearchQuery(BaseModel):
    query: str
    type_filter: Optional[str] = None
    tag_filter: Optional[str] = None

class SearchResult(BaseModel):
    items: List[KnowledgeItemResponse]
    ai_synthesis: str
    match_count: int
    query: str

class GraphNode(BaseModel):
    id: int
    label: str
    type: str
    category: str
    priority: str

class GraphLink(BaseModel):
    source: int
    target: int
    relation: str

class KnowledgeGraphResponse(BaseModel):
    nodes: List[GraphNode]
    links: List[GraphLink]

class TransformRequest(BaseModel):
    item_ids: List[int]
    target_format: str # "task_list", "draft_blog", "decision_matrix", "executive_summary"
