# 🧠 AI Second Brain

> An intelligent cross-platform application that connects notes, links, files, and ideas; extracts actionable insights; surfaces forgotten context; and turns captured knowledge into tasks, drafts, and decision frameworks.

Built for hackathons with universal compatibility across **Desktop (Windows, macOS, Linux)** and **Mobile Devices (iOS & Android)** powered by a **FastAPI** backend and **MySQL** database architecture.

---

## ✨ Core Features

1. **Smart Context Retrieval & AI Search**:
   - Query intent parsing: Search for `"Deadlines"` to immediately surface all time-sensitive tasks, milestone dates, and high-priority action items with AI rationale.
   - Intelligent scoring engine combining keyword relevance, temporal matching, and semantic intent.

2. **Automated AI Extraction & Auto-Tagging**:
   - Automatically parses date constraints, deadline dates (e.g., `"July 1, 2026"`), and bulleted to-do action items upon saving any note or concept.
   - Generates concise 1-2 sentence AI summaries for fast scanning.

3. **Interactive Knowledge Graph Visualizer**:
   - Visualizes relationships between notes, ideas, resources, and categories in an interactive 2D node-link topology map with real-time physics physics simulations.

4. **AI Action Studio**:
   - Select raw notes and ideas to generate structured output documents with one click:
     - 📋 Task Breakdown & Action Plans
     - ✍️ Draft Articles & Blog Posts
     - 📊 Executive Decision Briefings
     - ⚖️ Decision Evaluation Matrices

5. **Universal Device & Hackathon Portability**:
   - **Standalone Desktop GUI Window**: Powered by `pywebview` for a native application feel.
   - **Mobile Network Support**: Binds to local Wi-Fi interfaces so mobile devices can access the responsive app via local network URL.
   - **Smart Dual-Database Engine**: Connects seamlessly to **MySQL** (auto-creating `second_brain_db`), with zero-config portable **SQLite** fallback if MySQL server is offline on an evaluator's host machine.

---

## 🚀 Quick Start Guide

### 1. Clone & Install Dependencies
```bash
git clone https://github.com/your-username/ai-second-brain.git
cd ai-second-brain
pip install -r requirements.txt
```

### 2. Configure Database (Optional)
Copy `.env.example` to `.env` to customize MySQL settings:
```ini
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DB=second_brain_db
```
*(If MySQL is not installed or unreachable, the app automatically runs in portable SQLite mode!)*

### 3. Launch Application
```bash
python app.py
```
*Or double click `run_app.bat` on Windows.*

---

## 🛠️ Tech Stack

- **Backend**: Python 3.10+, FastAPI, Uvicorn, SQLAlchemy ORM, PyMySQL, Pydantic v2
- **Desktop Window**: pywebview (native desktop window rendering)
- **Frontend GUI**: Vanilla HTML5, Modern Glassmorphism CSS, Vanilla JS, HTML5 Canvas API
- **Database Engine**: MySQL / SQLite (Smart Dual-Engine)

---

## 📱 Mobile Access
When you run `python app.py`, the terminal outputs a **Mobile Network URL** (e.g., `http://192.168.1.50:8000`). Open this link on any mobile phone connected to the same Wi-Fi network for full mobile functionality!
