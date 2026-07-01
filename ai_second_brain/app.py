import os
import sys
import time
import socket
import threading
import uvicorn
from pathlib import Path

# Add project root to python path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from config import settings
from backend.database import engine, Base, SessionLocal, db_mode
from backend.models import KnowledgeItem, ItemConnection
from backend.ai_engine import AIEngine

def get_all_network_ips():
    """Gets all IPv4 addresses assigned to network adapters."""
    ip_list = []
    try:
        # Preferred method: Connect outward to detect default interface
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        primary = s.getsockname()[0]
        s.close()
        if primary and primary != "127.0.0.1":
            ip_list.append(primary)
    except Exception:
        pass

    try:
        # Fallback method: enumerate hostnames
        hostname = socket.gethostname()
        for ip in socket.gethostbyname_ex(hostname)[2]:
            if ip not in ip_list and not ip.startswith("127."):
                ip_list.append(ip)
    except Exception:
        pass

    return ip_list if ip_list else ["127.0.0.1"]

def seed_sample_data():
    """Seeds rich sample items for hackathon demonstration."""
    db = SessionLocal()
    try:
        if db.query(KnowledgeItem).count() == 0:
            print("🌱 Seeding initial sample hackathon knowledge records...")
            sample_items = [
                KnowledgeItem(
                    title="Hackathon Final Pitch Submission & Demo",
                    content="Need to prepare the final deck and record a 3-minute video demo showcasing AI Second Brain capabilities.\nDeadline: July 1, 2026 at 11:59 PM.\nTODO: Record video demo\nTODO: Submit GitHub repo link",
                    type="task",
                    category="Hackathon",
                    tags="hackathon,deadline,pitch,demo",
                    deadline="July 1, 2026",
                    priority="Urgent",
                    status="Active",
                    extracted_actions="• Record video demo\n• Submit GitHub repo link",
                    ai_summary="High-priority hackathon milestone submission with video demo and deck requirements."
                ),
                KnowledgeItem(
                    title="MySQL Database Architecture & Indexing Strategy",
                    content="Discussed optimized schema layout for storing knowledge items, vector embeddings, and item connections. Using SQLAlchemy ORM with dual engine support for maximum hackathon portability.",
                    type="note",
                    category="Research",
                    tags="database,mysql,sqlite,backend",
                    deadline=None,
                    priority="Medium",
                    status="Active",
                    extracted_actions="No explicit action items detected.",
                    ai_summary="Technical notes detailing the relational database schema and portable fallback architecture."
                ),
                KnowledgeItem(
                    title="AI Second Brain Concept & Graph Neural Links",
                    content="Idea for connecting notes based on semantic context rather than strict folder trees. When user searches 'Deadlines', surface all time-sensitive tasks regardless of category.",
                    type="idea",
                    category="Hackathon",
                    tags="ai,concept,idea,nlp",
                    deadline=None,
                    priority="High",
                    status="Active",
                    extracted_actions="• Implement semantic context retriever",
                    ai_summary="Core architectural idea behind contextual knowledge surfacing."
                ),
                KnowledgeItem(
                    title="FastAPI Documentation & Async Endpoints",
                    content="Reference documentation for building high-performance REST APIs with Python FastAPI, Pydantic v2 validation, and CORS support.",
                    type="link",
                    url="https://fastapi.tiangolo.com/",
                    category="Research",
                    tags="ai,fastapi,link,research",
                    deadline=None,
                    priority="Low",
                    status="Active",
                    extracted_actions="No explicit action items detected.",
                    ai_summary="External documentation reference for FastAPI backend services."
                )
            ]
            db.add_all(sample_items)
            db.commit()
            
            # Auto link item graph
            for item in db.query(KnowledgeItem).all():
                AIEngine.auto_link_items(db, item)
            print("✅ Sample hackathon data successfully seeded!")
    except Exception as e:
        print(f"Sample data seeding note: {e}")
    finally:
        db.close()

def run_fastapi_server():
    """Runs FastAPI uvicorn server in background thread."""
    from backend.server import app
    uvicorn.run(app, host=settings.HOST, port=settings.PORT, log_level="warning")

def main():
    print("=" * 60)
    print("🧠 AI SECOND BRAIN - DESKTOP & MOBILE APPLICATION")
    print(f"📡 Database Engine: {db_mode}")
    print("=" * 60)
    
    # 1. Initialize DB tables & seed sample data
    Base.metadata.create_all(bind=engine)
    seed_sample_data()
    
    # 2. Start Backend Server thread
    server_thread = threading.Thread(target=run_fastapi_server, daemon=True)
    server_thread.start()
    time.sleep(1.5) # Allow server to bind
    
    ips = get_all_network_ips()
    app_url = f"http://127.0.0.1:{settings.PORT}"
    
    print(f"\n🚀 Server running successfully!")
    print(f"💻 Desktop App URL: {app_url}")
    print(f"📱 Mobile Network URLs (Try these on your mobile phone on same Wi-Fi):")
    for ip in ips:
        print(f"   👉 http://{ip}:{settings.PORT}")
    print("\n💡 NOTE: Make sure to type 'http://' explicitly in your phone browser!\n")
    
    # 3. Launch Desktop GUI Window
    try:
        import webview
        print("🖥️ Launching Standalone Desktop GUI Window...")
        window = webview.create_window(
            title="AI Second Brain - Personal Knowledge Assistant",
            url=app_url,
            width=1280,
            height=850,
            resizable=True,
            min_size=(800, 600)
        )
        webview.start()
    except Exception as e:
        print(f"Desktop webview window notice: {e}")
        print("Opening default system web browser as desktop application window...")
        import webbrowser
        webbrowser.open(app_url)
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down AI Second Brain...")

if __name__ == "__main__":
    main()
