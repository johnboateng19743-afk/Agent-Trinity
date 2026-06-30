# 🜂 Trinity — Windows Installation Guide

> Step-by-step for Mr. Walker — no developer experience needed

---

## What You Need

- Windows 10 or 11 PC with internet
- Your GitHub account: `johnboateng19743-afk`

---

## Step 1: Install Python 3.11

1. Go to: https://www.python.org/downloads/release/python-3119/
2. Download **"Windows installer (64-bit)"**
3. Run the installer
4. ⚠️ **CHECK THE BOX** → "Add Python to PATH"
5. Click **Install Now**

**Verify:** Open Command Prompt, type `python --version` → should say `Python 3.11.x`

---

## Step 2: Install Git

1. Go to: https://git-scm.com/download/win
2. Download and run the installer
3. Click **Next** through all defaults
4. Close when done

---

## Step 3: Install Ollama (Local AI — FREE)

1. Go to: https://ollama.com/download
2. Download and install for Windows
3. After install, open a **new** Command Prompt and type:

```
ollama pull llama3.2:3b
```

Wait for the download to finish (~2 GB). This is Trinity's brain — 100% free, runs on your PC.

---

## Step 4: Install ffmpeg (for Audio)

1. Go to: https://www.gyan.dev/ffmpeg/builds/
2. Download **ffmpeg-release-essentials.zip**
3. Extract to `C:\ffmpeg`
4. Add to Windows PATH:
   - Press Windows key, type "environment", click **Edit environment variables**
   - Click **Environment Variables**
   - Under "User variables", select **Path**, click **Edit**
   - Click **New**, type `C:\ffmpeg\bin`
   - Click OK on all windows

---

## Step 5: Download Trinity

Open **Command Prompt**:

```
cd %USERPROFILE%
git clone https://github.com/johnboateng19743-afk/Agent-Trinity.git
cd Agent-Trinity
```

When asked for username: `johnboateng19743-afk`
When asked for password: paste your GitHub token (`ghp_...`)

---

## Step 6: Install Python Dependencies

```
python -m venv venv
venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

This takes 5–10 minutes. Wait for it to finish.

---

## Step 7: Start Trinity!

```
python -m trinity.main run
```

Say **"Trinity"** then ask a question. That's it! 🎉

**Other commands:**
- Check status: `python -m trinity.main status`
- Stop Trinity: `python -m trinity.main stop`

---

## Optional: Set Up Google (Calendar, Email, Maps)

This is optional — Trinity works without it.

1. Go to: https://console.cloud.google.com/
2. Select project **agent-trinity-500718**
3. Go to **APIs & Services → Credentials**
4. Click your OAuth 2.0 Client
5. Add redirect URI: `http://localhost:8400/auth/callback`
6. Go to **OAuth consent screen**
7. Add your Gmail as a **test user**
8. Save

---

## Optional: Add Cloud AI (for smarter answers)

Trinity uses local Llama 3.2 by default (free). You can add cloud AI for better answers:

| Provider | Cost | How |
|----------|------|-----|
| **OpenAI** (GPT-4o) | $5+ | Add billing at platform.openai.com/account/billing |
| **Anthropic** (Claude) | $5+ | Add billing at console.anthropic.com/settings/billing |

After adding credits, edit `.env` and change:
```
LLM_MODE=cloud
```

---

## Common Problems

| Problem | Fix |
|---------|-----|
| `python` not found | Reinstall Python with "Add to PATH" checked |
| `pip install` fails | Make sure you ran `venv\Scripts\activate` first |
| No sound | Install ffmpeg (Step 4), check speakers |
| `ollama` not found | Install Ollama (Step 3), restart Command Prompt |
| Llama is slow | Normal on first run — it gets faster after warming up |
| Microphone not working | Windows Settings → Privacy → Microphone → allow apps |

---

## Quick Install (PowerShell — if you already have Python + Git)

Open **PowerShell as Administrator**:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned -Force
cd $env:USERPROFILE
git clone https://github.com/johnboateng19743-afk/Agent-Trinity.git
cd Agent-Trinity
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
ollama pull llama3.2:3b
python -m trinity.main run
```

---

*Trinity — Your voice. Your machine. Your agent.*
