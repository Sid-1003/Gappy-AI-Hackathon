import os
from pathlib import Path
from typing import List
from fastapi import FastAPI, Depends, HTTPException, Query, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from backend.database import get_db, Base, engine, db_mode
from backend.models import KnowledgeItem, ItemConnection, AIInsight
from backend.schemas import (
    KnowledgeItemCreate, KnowledgeItemUpdate, KnowledgeItemResponse,
    SearchQuery, SearchResult, KnowledgeGraphResponse, GraphNode, GraphLink, TransformRequest
)
from backend.ai_engine import AIEngine

# Create database tables if not created
Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Second Brain API", version="2.0.0")

# Setup CORS for cross-device & mobile access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- API ENDPOINTS ----------------

@app.get("/api/status")
def get_system_status():
    return {
        "status": "online",
        "database_engine": db_mode,
        "app": "AI Second Brain"
    }

@app.post("/api/items", response_model=KnowledgeItemResponse, status_code=status.HTTP_201_CREATED)
def create_item(item_in: KnowledgeItemCreate, db: Session = Depends(get_db)):
    # Auto-extract AI metadata (deadlines, actions, tags, summary)
    ai_meta = AIEngine.extract_metadata(item_in.title, item_in.content, item_in.type)
    
    final_tags = item_in.tags if item_in.tags else ai_meta["suggested_tags"]
    final_deadline = item_in.deadline if item_in.deadline else ai_meta["deadline"]
    
    db_item = KnowledgeItem(
        title=item_in.title,
        content=item_in.content,
        type=item_in.type,
        url=item_in.url,
        category=item_in.category or "General",
        tags=final_tags,
        deadline=final_deadline,
        priority=item_in.priority or "Medium",
        status=item_in.status or "Active",
        extracted_actions=ai_meta["extracted_actions"],
        ai_summary=ai_meta["ai_summary"]
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    
    # Trigger auto graph connection linking
    try:
        AIEngine.auto_link_items(db, db_item)
    except Exception as e:
        print("Auto link error:", e)
        
    return db_item


@app.get("/api/items", response_model=List[KnowledgeItemResponse])
def get_items(
    type: str = Query(None),
    category: str = Query(None),
    tag: str = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(KnowledgeItem)
    if type and type.lower() != "all":
        query = query.filter(KnowledgeItem.type == type)
    if category and category.lower() != "all":
        query = query.filter(KnowledgeItem.category == category)
    if tag and tag.lower() != "all":
        query = query.filter(KnowledgeItem.tags.contains(tag))
        
    items = query.order_by(KnowledgeItem.created_at.desc()).all()
    return items


@app.get("/api/items/{item_id}", response_model=KnowledgeItemResponse)
def get_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(KnowledgeItem).filter(KnowledgeItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@app.put("/api/items/{item_id}", response_model=KnowledgeItemResponse)
def update_item(item_id: int, item_in: KnowledgeItemUpdate, db: Session = Depends(get_db)):
    db_item = db.query(KnowledgeItem).filter(KnowledgeItem.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
        
    update_data = item_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_item, key, value)
        
    # Re-extract AI metadata if content or title changed
    if "content" in update_data or "title" in update_data:
        ai_meta = AIEngine.extract_metadata(db_item.title, db_item.content, db_item.type)
        if not db_item.deadline:
            db_item.deadline = ai_meta["deadline"]
        db_item.extracted_actions = ai_meta["extracted_actions"]
        db_item.ai_summary = ai_meta["ai_summary"]
        
    db.commit()
    db.refresh(db_item)
    return db_item


@app.delete("/api/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: int, db: Session = Depends(get_db)):
    db_item = db.query(KnowledgeItem).filter(KnowledgeItem.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    db.delete(db_item)
    db.commit()
    return None


@app.post("/api/search", response_model=SearchResult)
def search_items(search_in: SearchQuery, db: Session = Depends(get_db)):
    items, synthesis = AIEngine.search_and_synthesize(
        db, search_in.query, search_in.type_filter, search_in.tag_filter
    )
    return SearchResult(
        items=items,
        ai_synthesis=synthesis,
        match_count=len(items),
        query=search_in.query
    )


@app.get("/api/graph", response_model=KnowledgeGraphResponse)
def get_knowledge_graph(db: Session = Depends(get_db)):
    items = db.query(KnowledgeItem).all()
    connections = db.query(ItemConnection).all()
    
    nodes = [
        GraphNode(
            id=item.id,
            label=item.title,
            type=item.type,
            category=item.category,
            priority=item.priority
        ) for item in items
    ]
    
    links = [
        GraphLink(
            source=conn.source_id,
            target=conn.target_id,
            relation=conn.relation_type
        ) for conn in connections
    ]
    
    return KnowledgeGraphResponse(nodes=nodes, links=links)


@app.post("/api/ai/transform")
def transform_knowledge(req: TransformRequest, db: Session = Depends(get_db)):
    items = db.query(KnowledgeItem).filter(KnowledgeItem.id.in_(req.item_ids)).all()
    if not items:
        raise HTTPException(status_code=400, detail="No valid items selected for transformation")
        
    result_doc = AIEngine.transform_knowledge(items, req.target_format)
    return {
        "format": req.target_format,
        "document": result_doc,
        "source_count": len(items)
    }


@app.post("/api/ai/merge")
def merge_similar_notes(req: TransformRequest, db: Session = Depends(get_db)):
    items = db.query(KnowledgeItem).filter(KnowledgeItem.id.in_(req.item_ids)).all()
    if not items:
        raise HTTPException(status_code=400, detail="No items selected to merge")
    merged_summary = AIEngine.merge_summarize_notes(items)
    return {"merged_summary": merged_summary}


@app.get("/api/insights")
def get_ai_insights(db: Session = Depends(get_db)):
    items = db.query(KnowledgeItem).all()
    deadlines = [i for i in items if i.deadline or i.priority in ['Urgent', 'High']]
    ideas = [i for i in items if i.type == 'idea']
    links = [i for i in items if i.type == 'link' or i.url]
    
    insights = [
        {
            "id": 1,
            "title": f"⏱️ Action Required: {len(deadlines)} Time-Sensitive Items",
            "description": f"Surfaced context: You have {len(deadlines)} notes with active deadlines or urgent priority. Make sure to review project milestones.",
            "insight_type": "Deadline Warning"
        },
        {
            "id": 2,
            "title": f"💡 Idea Hub: {len(ideas)} Concepts Ready for Synthesis",
            "description": "Connected knowledge: Turn your captured ideas into actionable drafts or project task lists in the AI Action Center.",
            "insight_type": "Idea Synthesis"
        },
        {
            "id": 3,
            "title": f"🔗 Knowledge Vault: {len(links)} External Links Indexed",
            "description": "Cross-reference active: Links are integrated into your smart search network and knowledge connection map.",
            "insight_type": "Resource Tracker"
        }
    ]
    return insights

# Mount Static Files for Mobile & Desktop Frontend
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

@app.get("/")
def serve_index():
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return JSONResponse({"message": "AI Second Brain API running. Frontend assets placing..."})
