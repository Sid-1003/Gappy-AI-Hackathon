import re
import datetime
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from backend.models import KnowledgeItem, ItemConnection, AIInsight

class AIEngine:
    @staticmethod
    def extract_metadata(title: str, content: str, item_type: str) -> Dict[str, Any]:
        """Auto-extracts deadlines, action items, tags, and summary points from content."""
        full_text = f"{title}\n{content}"
        
        # 1. Deadline Detection
        deadline = None
        date_patterns = [
            r'(?:due|deadline|by|before|submit|target|completion)[:\s]+([A-Za-z0-9\s,]{3,20}\d{4})',
            r'(?:due|deadline|by|before)[:\s]+(today|tomorrow|next week|end of week|this friday|\d{1,2}/\d{1,2}/\d{2,4}|\d{4}-\d{2}-\d{2})',
            r'(July \d{1,2},? \d{4}|June \d{1,2},? \d{4}|August \d{1,2},? \d{4}|\d{4}-\d{2}-\d{2})'
        ]
        for pattern in date_patterns:
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                deadline = match.group(1).strip()
                break
        
        # 2. Action Items Extraction
        actions = []
        lines = content.split('\n')
        for line in lines:
            line_str = line.strip()
            if re.match(r'^[-*•\d+.]\s*\[?\s*\]?\s*(todo|task|need to|must|should|fix|build|implement|design|write|send|review)', line_str, re.IGNORECASE) or 'TODO' in line_str or 'FIXME' in line_str:
                clean_action = re.sub(r'^[-*•\d+.]\s*\[?\s*\]?\s*', '', line_str)
                actions.append(clean_action)
            elif any(keyword in line_str.lower() for keyword in ['need to', 'must deliver', 'action item:', 'deadline:']):
                actions.append(line_str)
                
        extracted_actions = "\n".join([f"• {a}" for a in actions[:6]]) if actions else "No explicit action items detected."

        # 3. AI Summary
        sentences = [s.strip() for s in re.split(r'[.!?]\s+', content) if len(s.strip()) > 10]
        if sentences:
            ai_summary = sentences[0] + ("." if not sentences[0].endswith('.') else "")
            if len(sentences) > 1:
                ai_summary += " " + sentences[1] + ("." if not sentences[1].endswith('.') else "")
        else:
            ai_summary = content[:150] + ("..." if len(content) > 150 else "")

        # 4. Auto Tagging
        extracted_tags = set()
        topic_keywords = {
            'hackathon': ['hackathon', 'pitch', 'demo', 'judges', 'submission'],
            'ai': ['ai', 'llm', 'fastapi', 'nlp', 'model', 'machine learning', 'embeddings'],
            'deadline': ['deadline', 'due', 'urgent', 'milestone', 'schedule'],
            'design': ['design', 'ui', 'ux', 'css', 'frontend', 'aesthetic'],
            'database': ['database', 'mysql', 'sqlite', 'sql', 'backend', 'orm'],
            'research': ['research', 'paper', 'link', 'article', 'reference']
        }
        lowered = full_text.lower()
        for tag, kw_list in topic_keywords.items():
            if any(kw in lowered for kw in kw_list):
                extracted_tags.add(tag)
        
        return {
            "deadline": deadline,
            "extracted_actions": extracted_actions,
            "ai_summary": ai_summary,
            "suggested_tags": ",".join(list(extracted_tags))
        }

    @staticmethod
    def search_and_synthesize(db: Session, query: str, type_filter: str = None, tag_filter: str = None) -> Tuple[List[KnowledgeItem], str]:
        """Performs intelligent semantic context retrieval and generates AI synthesis."""
        items = db.query(KnowledgeItem).all()
        q_lower = query.lower().strip()
        
        # Intent Check
        is_deadline_intent = any(w in q_lower for w in ['deadline', 'due', 'date', 'urgent', 'schedule', 'time', 'milestone', 'pending'])
        is_idea_intent = any(w in q_lower for w in ['idea', 'concept', 'thought', 'brainstorm'])
        is_link_intent = any(w in q_lower for w in ['link', 'url', 'resource', 'site', 'article'])
        
        scored_items = []
        for item in items:
            # Apply strict filters if provided
            if type_filter and type_filter.lower() != "all" and item.type.lower() != type_filter.lower():
                continue
            if tag_filter and tag_filter.lower() != "all" and tag_filter.lower() not in item.tags.lower():
                continue
                
            score = 0.0
            full_text = f"{item.title} {item.content} {item.tags} {item.category} {item.deadline or ''} {item.type}".lower()
            
            # Direct text matching
            if q_lower in full_text:
                score += 10.0
            
            # Word token matches
            words = q_lower.split()
            for w in words:
                if len(w) > 2 and w in full_text:
                    score += 3.0
            
            # Special Intent Scoring
            if is_deadline_intent:
                if item.deadline or item.priority in ['Urgent', 'High']:
                    score += 15.0
                if any(k in full_text for k in ['due', 'deadline', 'july', 'june', 'submit', 'deliver']):
                    score += 8.0
                    
            if is_idea_intent and item.type.lower() == 'idea':
                score += 12.0
                
            if is_link_intent and (item.type.lower() == 'link' or item.url):
                score += 12.0
                
            if score > 0 or not q_lower:
                scored_items.append((score if q_lower else 1.0, item))
                
        # Sort by score descending
        scored_items.sort(key=lambda x: x[0], reverse=True)
        matched_items = [item for score, item in scored_items]
        
        # Generate AI Synthesis
        if not matched_items:
            synthesis = f"AI Analysis: No exact items found matching '{query}'. Try searching for broader terms like 'Notes', 'Ideas', or 'Deadlines'."
        elif is_deadline_intent:
            items_with_dates = [i for i in matched_items if i.deadline or i.priority in ['Urgent', 'High']]
            count = len(items_with_dates) if items_with_dates else len(matched_items)
            top_item = matched_items[0]
            synthesis = f"🎯 AI Context Synthesis for '{query}': Identified {count} high-priority time-sensitive items. Key item: '{top_item.title}' (Priority: {top_item.priority}, Deadline: {top_item.deadline or 'Upcoming'})."
        else:
            types_found = list(set([i.type.capitalize() for i in matched_items[:5]]))
            synthesis = f"🧠 AI Context Synthesis for '{query}': Connected {len(matched_items)} items across categories ({', '.join(types_found)}). Top insight extracted from '{matched_items[0].title}'."
            
        return matched_items, synthesis

    @staticmethod
    def auto_link_items(db: Session, item: KnowledgeItem):
        """Automatically builds item connection relationships based on shared tags and keywords."""
        all_items = db.query(KnowledgeItem).filter(KnowledgeItem.id != item.id).all()
        item_tags = set([t.strip().lower() for t in item.tags.split(',') if t.strip()])
        
        for other in all_items:
            other_tags = set([t.strip().lower() for t in other.tags.split(',') if t.strip()])
            common_tags = item_tags.intersection(other_tags)
            
            # Calculate weight
            weight = len(common_tags) * 1.5
            if item.category.lower() == other.category.lower() and item.category.lower() != "general":
                weight += 1.0
            if item.type == "task" and other.type == "idea":
                weight += 0.5
                
            if weight >= 1.0:
                # Check existing connection
                existing = db.query(ItemConnection).filter(
                    ((ItemConnection.source_id == item.id) & (ItemConnection.target_id == other.id)) |
                    ((ItemConnection.source_id == other.id) & (ItemConnection.target_id == item.id))
                ).first()
                if not existing:
                    conn = ItemConnection(source_id=item.id, target_id=other.id, relation_type="related_concept", weight=weight)
                    db.add(conn)
        db.commit()

    @staticmethod
    def transform_knowledge(items: List[KnowledgeItem], format_type: str) -> str:
        """Transforms raw notes into structured tasks, drafts, or decision frameworks."""
        titles = [i.title for i in items]
        contents = "\n\n".join([f"--- {i.title} ({i.type.upper()}) ---\n{i.content}" for i in items])
        
        if format_type == "task_list":
            output = f"# 📋 AI Synthesized Action Plan & Task Breakdown\n\n**Source Knowledge Items**: {', '.join(titles)}\n\n## Immediate Action Items\n"
            for item in items:
                output += f"\n### From: {item.title}\n"
                if item.extracted_actions and item.extracted_actions != "No explicit action items detected.":
                    output += item.extracted_actions + "\n"
                else:
                    output += f"• Review and integrate concepts from {item.title}\n• Execute primary milestone\n"
            return output
            
        elif format_type == "draft_blog":
            output = f"# ✍️ AI Draft Generator: Synthesized Article\n\n**Topic**: {titles[0] if titles else 'Knowledge Synthesis'}\n\n## Introduction\nIn today's fast-moving environment, connecting distinct ideas into cohesive frameworks is key. Based on our second brain insights regarding {', '.join(titles[:3])}, here is the comprehensive breakdown.\n\n## Core Concepts & Insights\n{contents}\n\n## Conclusion & Next Steps\nBy bringing these notes together, we establish a robust foundation for building actionable outcomes."
            return output
            
        elif format_type == "executive_summary":
            output = f"# 📊 Executive Decision Briefing\n\n**Generated On**: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}\n**Analyzed Sources**: {len(items)} items\n\n## Key Takeaways\n"
            for i in items:
                output += f"- **{i.title}**: {i.ai_summary or i.content[:100]}\n"
            output += f"\n## Strategic Recommendation\nBased on cross-analysis, prioritize deadline-driven tasks and integrate linked resources to accelerate execution."
            return output
            
        elif format_type == "formal_mail":
            output = f"Subject: Synthesis Briefing: {', '.join(titles[:2])} Updates\n\nDear Team,\n\nI hope this message finds you well.\n\nI am writing to share a synthesized update drawing from our active knowledge vault records: {', '.join(titles)}.\n\nHere are the critical summaries:\n"
            for i in items:
                output += f"- {i.title}: {i.ai_summary or i.content[:100]}\n"
            if any(i.deadline for i in items):
                output += "\nPlease note the upcoming deadlines:\n"
                for i in items:
                    if i.deadline:
                        output += f"- {i.title}: Due by {i.deadline}\n"
            output += "\nShould you have any questions or require clarification on these updates, please let me know.\n\nBest regards,\n[Your Name]\nAI Second Brain User"
            return output
            
        else: # decision_matrix
            output = f"# ⚖️ Decision Evaluation Matrix\n\n| Item / Option | Type | Priority | Deadline | Key AI Insight |\n| --- | --- | --- | --- | --- |\n"
            for i in items:
                output += f"| {i.title} | {i.type} | {i.priority} | {i.deadline or 'N/A'} | {i.ai_summary[:60] if i.ai_summary else 'Active context'} |\n"
            return output

    @staticmethod
    def merge_summarize_notes(items: List[KnowledgeItem]) -> str:
        """Merges multiple similar notes into one single cohesive summary."""
        if not items:
            return "No notes provided to merge."
        
        titles = [i.title for i in items]
        
        core_themes = []
        action_items = []
        milestones = []
        
        for item in items:
            if item.ai_summary:
                core_themes.append(item.ai_summary)
            else:
                sentences = [s.strip() for s in item.content.split('.') if len(s.strip()) > 15]
                if sentences:
                    core_themes.append(sentences[0])
            
            if item.extracted_actions and item.extracted_actions != "No explicit action items detected.":
                actions = [a.strip().replace('• ', '') for a in item.extracted_actions.split('\n') if a.strip()]
                action_items.extend(actions)
                
            if item.deadline:
                milestones.append(f"'{item.title}' due by {item.deadline}")
                
        unique_themes = list(set(core_themes))
        unique_actions = list(set(action_items))
        
        synthesis = f"### 🧠 Consolidated Core Themes\n"
        for idx, theme in enumerate(unique_themes[:4], 1):
            synthesis += f"{idx}. {theme}\n"
            
        if milestones:
            synthesis += f"\n### 📅 Consolidated Milestones & Timeline\n"
            for m in milestones[:3]:
                synthesis += f"- {m}\n"
                
        if unique_actions:
            synthesis += f"\n### 🎯 Unified Action Plan\n"
            for act in unique_actions[:6]:
                synthesis += f"• {act}\n"
        else:
            synthesis += f"\n### 🎯 Unified Action Plan\n• Review connected knowledge files and formulate project strategy.\n"
            
        synthesis += f"\n### 💡 Strategic Overview\nBy combining these connected records ({len(items)} source files), we establish a single unified reference point. These inputs align closely around active hackathon/project milestones and should be managed as a single stream of work."
        
        return synthesis
