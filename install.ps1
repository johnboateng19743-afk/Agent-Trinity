# Trinity Installer Script — Run this in PowerShell
# ==========================================
# Prerequisites: Python 3.11+ and Git must be installed first
#
# HOW TO RUN:
# 1. Open PowerShell
# 2. Run: Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
# 3. Run: cd $HOME
# 4. Run: git clone https://github.com/johnboateng19743-afk/Agent-Trinity.git
# 5. Run: cd Agent-Trinity
# 6. Run: .\install.ps1

Write-Host ""
Write-Host "  🜂 Trinity Installer" -ForegroundColor Cyan
Write-Host "  Voice-First AI Agent — 100% Free, Runs Locally" -ForegroundColor DarkGray
Write-Host ""

# ── Check Prerequisites ──
Write-Host "  Checking prerequisites..." -ForegroundColor Yellow

$missing = @()

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    $missing += "Python 3.11+ (https://www.python.org/downloads/)"
}
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    $missing += "Git (https://git-scm.com/download/win)"
}

if ($missing.Count -gt 0) {
    Write-Host "  ❌ Missing prerequisites:" -ForegroundColor Red
    foreach ($item in $missing) {
        Write-Host "     - $item" -ForegroundColor Red
    }
    Write-Host ""
    Write-Host "  Please install them and run this script again." -ForegroundColor Yellow
    exit 1
}

Write-Host "  ✅ Python found: $(python --version 2>&1)" -ForegroundColor Green
Write-Host "  ✅ Git found" -ForegroundColor Green
Write-Host ""

# ── Create Virtual Environment ──
Write-Host "  ⏳ Creating virtual environment..." -ForegroundColor Yellow
python -m venv venv
Write-Host "  ✅ Virtual environment created" -ForegroundColor Green

# ── Activate venv ──
& .\venv\Scripts\Activate.ps1

# ── Install Python Dependencies ──
Write-Host "  ⏳ Installing Python dependencies (5-10 minutes)..." -ForegroundColor Yellow
pip install --upgrade pip --quiet
pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ❌ Failed to install dependencies. Check the errors above." -ForegroundColor Red
    exit 1
}
Write-Host "  ✅ Dependencies installed" -ForegroundColor Green

# ── Check Ollama ──
Write-Host ""
Write-Host "  Checking Ollama (local AI)..." -ForegroundColor Yellow

if (Get-Command ollama -ErrorAction SilentlyContinue) {
    Write-Host "  ✅ Ollama found" -ForegroundColor Green
    
    # Pull the AI model
    Write-Host "  ⏳ Downloading Llama 3.2 AI model (2 GB, one-time download)..." -ForegroundColor Yellow
    ollama pull llama3.2:3b
    Write-Host "  ✅ Llama 3.2 downloaded" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  Ollama not found" -ForegroundColor Yellow
    Write-Host "     Please install it from https://ollama.com/download" -ForegroundColor Yellow
    Write-Host "     Then run: ollama pull llama3.2:3b" -ForegroundColor Yellow
    Write-Host "     Trinity will use cloud AI as fallback until Ollama is installed." -ForegroundColor DarkGray
}

# ── Check ffmpeg ──
if (Get-Command ffplay -ErrorAction SilentlyContinue) {
    Write-Host "  ✅ ffmpeg found" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  ffmpeg not found (needed for audio playback)" -ForegroundColor Yellow
    Write-Host "     Download from https://www.gyan.dev/ffmpeg/builds/" -ForegroundColor Yellow
    Write-Host "     Extract to C:\ffmpeg and add C:\ffmpeg\bin to your PATH" -ForegroundColor Yellow
}

# ── Create data directory ──
$dataDir = "$HOME\.trinity\data"
New-Item -ItemType Directory -Force -Path $dataDir | Out-Null
Write-Host "  ✅ Data directory created: $dataDir" -ForegroundColor Green

# ── Done ──
Write-Host ""
Write-Host "  ══════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  🎉 Trinity is installed and ready!" -ForegroundColor Green
Write-Host "  ══════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "  To start Trinity:" -ForegroundColor White
Write-Host "    cd $HOME\Agent-Trinity" -ForegroundColor Yellow
Write-Host "    .\venv\Scripts\Activate.ps1" -ForegroundColor Yellow
Write-Host "    python -m trinity.main run" -ForegroundColor Yellow
Write-Host ""
Write-Host "  Other commands:" -ForegroundColor White
Write-Host "    python -m trinity.main status   (check if running)" -ForegroundColor DarkGray
Write-Host "    python -m trinity.main stop     (stop Trinity)" -ForegroundColor DarkGray
Write-Host ""
