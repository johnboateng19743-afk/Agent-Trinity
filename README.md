# 🜂 Trinity — Voice-First AI Agent

> *Your voice. Your machine. Your agent.*

Trinity is a voice-first AI agent that lives on your Windows machine. She can hear you, think about what you need, and act on your behalf across your entire digital life: files, folders, documents, calendar, email, maps, location, and Google services.

## ✨ Features

- 🎤 **Voice-First** — Say "Trinity" to activate, then speak naturally
- 📁 **File System Control** — Read, create, edit, move, and delete files by voice
- 📅 **Google Calendar** — View, create, and manage events
- 📧 **Gmail** — Read, search, compose, and reply to emails
- 🗺️ **Maps & Location** — Find places, get directions
- 🧠 **Persistent Memory** — Remembers facts, preferences, and conversations
- ☁️ **Hybrid Intelligence** — Cloud LLM (GPT-4o) + Local LLM (Ollama) for offline fallback
- 🔄 **Self-Updating** — Atomic updates with automatic rollback
- 🔒 **Privacy-First** — Local-first architecture, data stays on your machine

## 🖥️ Requirements

| Requirement | Version |
|---|---|
| Windows | 10/11 (64-bit) |
| Python | 3.11+ |
| Microphone | Any |
| Speakers | Any |
| Internet | Required for cloud features |

## 🚀 Quick Start

### 1. Clone the repository
```powershell
git clone https://github.com/johnboateng19743-afk/Agent-Trinity.git
cd Agent-Trinity
```

### 2. Create virtual environment
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies
```powershell
pip install -r requirements.txt
```

### 4. Configure your environment
```powershell
copy .env.example .env
notepad .env
```

### 5. (Optional) Install Ollama for offline mode
```powershell
# Download from https://ollama.com/download/windows
ollama pull qwen2.5:1.5b
ollama pull llama3.2:3b
```

### 6. Run Trinity
```powershell
python -m trinity.main
```

## 🗣️ Example Commands

| Voice Command | What Trinity Does |
|---|---|
| "Trinity, what's in my Downloads?" | Lists files in Downloads folder |
| "Find all PDFs from last week" | Searches for recent PDF files |
| "Move quarterly-report.docx to Documents/Reports" | Moves the file |
| "What's on my calendar today?" | Shows today's schedule |
| "Read my latest emails" | Reads recent Gmail messages |
| "Email Sarah: Can we reschedule?" | Drafts an email for review |
| "Where's the nearest coffee shop?" | Finds nearby coffee shops |
| "Trinity, remember my deadline is July 15" | Stores in persistent memory |

## 🔧 Configuration

All configuration lives in the `.env` file. Key settings:

| Variable | Description |
|---|---|
| `ELEVENLABS_API_KEY` | ElevenLabs TTS API key |
| `OPENAI_API_KEY` | OpenAI API key (primary brain) |
| `ANTHROPIC_API_KEY` | Anthropic API key (fallback brain) |
| `GOOGLE_CLIENT_ID` | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | Google OAuth client secret |
| `GOOGLE_MAPS_API_KEY` | Google Maps API key |
| `TRINITY_USER_NAME` | Your name — Trinity will use it |

## 🏗️ Architecture

```
Trinity Agent
├── Voice Engine (STT + TTS + Wake Word + VAD)
├── Orchestrator (Intent Router + Context Manager)
├── Skills (FileSystem, Calendar, Email, Drive, Maps, Apps)
├── Memory (ChromaDB Vector + SQLite + User Profile)
├── LLM Router (Cloud-first: GPT-4o → Claude → Ollama offline)
├── Integrations (Google OAuth + Credential Store)
├── UI (System Tray + Voice Overlay + Dashboard)
├── Updates (Auto-update with rollback)
└── Watchdog (Crash detection + restart)
```

## 🧪 Running Tests

```powershell
pip install pytest pytest-asyncio
pytest tests/ -v
```

## 📋 Hardware Note

Trinity is configured for **cloud-first** operation on Mr. Walker's hardware (Intel i5-8250U / 8GB RAM / no dedicated GPU). This means:

- **GPT-4o (cloud)** handles 95% of requests
- **Local LLMs** are small (1.5B–3B params) and used only as offline fallback
- If you upgrade to a GPU, set `TRINITY_GPU_ENABLED=true` for faster local inference

## 📄 License

MIT

---

*Trinity — Your voice. Your machine. Your agent.*
