# 🜂 Trinity — Windows Installation Guide

> Step-by-step instructions for Mr. Walker to install Trinity on a Windows PC

---

## What You Need Before Starting

1. **Windows 10 or 11** PC with internet
2. **Your GitHub account** — `johnboateng19743-afk`
3. **A GitHub Personal Access Token** (to download the code)

---

## Step 1: Create a GitHub Personal Access Token

1. Go to: https://github.com/settings/tokens
2. Click **"Generate new token (classic)"**
3. Name it: `Trinity Install`
4. Check the box: **repo** (full control of private repositories)
5. Click **Generate token** at the bottom
6. **Copy the token** (starts with `ghp_`) — you'll need it below

---

## Step 2: Install Python 3.11

1. Go to: https://www.python.org/downloads/release/python-3119/
2. Download **"Windows installer (64-bit)"**
3. Run the installer
4. ⚠️ **CHECK THE BOX** that says "Add Python to PATH"
5. Click **Install Now**
6. After it finishes, close the installer

**Verify it worked:**
- Open **Command Prompt** (press Windows key, type `cmd`, press Enter)
- Type: `python --version`
- You should see: `Python 3.11.x`

---

## Step 3: Install Git

1. Go to: https://git-scm.com/download/win
2. Download and run the installer
3. Click **Next** through all defaults
4. When it finishes, close the installer

---

## Step 4: Download Trinity

Open **Command Prompt** and type these commands one at a time:

```
cd %USERPROFILE%
git clone https://github.com/johnboateng19743-afk/Agent-Trinity.git
cd Agent-Trinity
```

When it asks for your username, type: `johnboateng19743-afk`
When it asks for your password, paste your **GitHub token** (the `ghp_...` one)

---

## Step 5: Install Dependencies

Still in Command Prompt, inside the Agent-Trinity folder:

```
python -m venv venv
venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

This will download and install all the Python packages Trinity needs. It may take 5–10 minutes.

---

## Step 6: Install Ollama (for Offline AI)

Ollama lets Trinity work even when you have no internet.

1. Go to: https://ollama.com/download
2. Download and install for Windows
3. After it installs, open a **new** Command Prompt and type:

```
ollama pull qwen2.5:1.5b
```

This downloads a small AI model (about 1 GB). Wait for it to finish.

---

## Step 7: Install ffmpeg (for Audio)

1. Go to: https://www.gyan.dev/ffmpeg/builds/
2. Download **ffmpeg-release-essentials.zip**
3. Extract the zip to `C:\ffmpeg`
4. Add `C:\ffmpeg\bin` to your Windows PATH:
   - Press Windows key, type "environment", click **"Edit environment variables"**
   - Click **"Environment Variables"**
   - Under "User variables", select **Path**, click **Edit**
   - Click **New**, type `C:\ffmpeg\bin`
   - Click OK on all windows

**Verify:** Open a new Command Prompt, type `ffplay` — you should see usage info (not an error)

---

## Step 8: Fix Your API Keys

You need to add credits to your API accounts before Trinity can talk to AI:

### OpenAI (Primary AI)
1. Go to: https://platform.openai.com/account/billing
2. Add a payment method and add at least **$5 credit**
3. Your API key is already saved in the `.env` file

### Anthropic (Backup AI)
1. Go to: https://console.anthropic.com/settings/billing
2. Add a payment method and add at least **$5 credit**
3. Your API key is already saved in the `.env` file

### ElevenLabs (Voice)
1. Go to: https://elevenlabs.io/app/settings/api-keys
2. Your current key may be expired. Generate a **new API key**
3. Copy the new key
4. Open the file `.env` in the Agent-Trinity folder with Notepad
5. Replace the `ELEVENLABS_API_KEY=...` line with your new key
6. Save the file

---

## Step 9: Set Up Google OAuth

1. Go to: https://console.cloud.google.com/
2. Select project **agent-trinity-500718**
3. Go to **APIs & Services → Credentials**
4. Click your OAuth 2.0 Client
5. Under **Authorized redirect URIs**, add:
   ```
   http://localhost:8400/auth/callback
   ```
6. Go to **APIs & Services → OAuth consent screen**
7. Under **Test users**, add your Gmail address
8. Click Save

---

## Step 10: Start Trinity!

Open **Command Prompt**:

```
cd %USERPROFILE%\Agent-Trinity
venv\Scripts\activate
python -m trinity.main run
```

Trinity will start listening. Say **"Trinity"** to wake it up, then ask a question.

To check if it's running:
```
python -m trinity.main status
```

To stop it:
```
python -m trinity.main stop
```

---

## Common Problems

| Problem | Fix |
|---------|-----|
| `python` not found | Reinstall Python with "Add to PATH" checked |
| `pip install` fails | Make sure you ran `venv\Scripts\activate` first |
| No sound | Install ffmpeg (Step 7) and check your speakers |
| "Insufficient quota" error | Add credits to your OpenAI/Anthropic account (Step 8) |
| "Unauthorized" error from ElevenLabs | Generate a new API key (Step 8) |
| Google login fails | Add redirect URI and test user (Step 9) |
| Microphone not working | Check Windows Settings → Privacy → Microphone → allow apps |
| `ollama` not found | Install Ollama (Step 6) or skip it (Trinity will use cloud AI) |

---

## Quick Start (One-Line Install)

If you have Python and Git already, open **PowerShell as Administrator** and run:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned -Force
cd $env:USERPROFILE
git clone https://github.com/johnboateng19743-afk/Agent-Trinity.git
cd Agent-Trinity
.\install.ps1
```

---

*Trinity — Your voice. Your machine. Your agent.*
