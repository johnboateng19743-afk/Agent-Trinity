@echo off
:: Trinity — Background Voice Assistant
:: This script starts Trinity in voice mode, hidden from view.
:: Trinity runs in the background — just say "Trinity" to activate.
::
:: To auto-start on boot:
:: 1. Press Win+R, type shell:startup, press Enter
:: 2. Copy this file into the Startup folder

cd /d "%~dp0"
call venv\Scripts\activate.bat
pythonw -m trinity.main voice
