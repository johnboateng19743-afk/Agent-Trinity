@echo off
:: Trinity — Web Chat UI (background)
:: Starts the web chat interface. Open http://localhost:8400 in your browser.
::
:: To auto-start on boot:
:: 1. Press Win+R, type shell:startup, press Enter
:: 2. Copy this file into the Startup folder

cd /d "%~dp0"
call venv\Scripts\activate.bat
start "" http://localhost:8400
pythonw -m trinity.main run
