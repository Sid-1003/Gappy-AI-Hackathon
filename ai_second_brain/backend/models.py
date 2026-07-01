import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from backend.database import Base

class KnowledgeItem(Base):
    __tablename__ = "knowledge_items"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    content = Column(Text, nullable=False)
    type = Column(String(50), nullable=False, index=True) # note, link, idea, task, draft
    url = Column(String(512), nullable=True)
    category = Column(String(100), default="General", index=True)
    tags = Column(String(255), default="", index=True) # Comma-separated tags e.g. "hackathon,ai,deadline"
    
    # AI & Metadata Fields
    deadline = Column(String(100), nullable=True, index=True) # ISO Date string or human deadline e.g. "2026-07-01", "Next Monday"
    priority = Column(String(50), default="Medium") # Low, Medium, High, Urgent
    status = Column(String(50), default="Active") # Active, Draft, Archived, Completed
    extracted_actions = Column(Text, nullable=True) # JSON or bullet points of actions
    ai_summary = Column(Text, nullable=True) # Concise AI context summary
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class ItemConnection(Base):
    __tablename__ = "item_connections"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("knowledge_items.id", ondelete="CASCADE"), nullable=False)
    target_id = Column(Integer, ForeignKey("knowledge_items.id", ondelete="CASCADE"), nullable=False)
    relation_type = Column(String(100), default="related") # related, references, derived_task, linked_idea
    weight = Column(Float, default=1.0)


class AIInsight(Base):
    __tablename__ = "ai_insights"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    insight_type = Column(String(50), default="Context Spotter") # Deadline Warning, Knowledge Gap, Connected Topic
    related_item_ids = Column(String(255), default="") # Comma-separated item IDs
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
