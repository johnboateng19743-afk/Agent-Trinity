' Trinity — Hidden Background Launcher
' Double-click this to start Trinity in voice mode with NO visible window.
' Trinity runs silently — just say "Trinity" to activate.
'
' To auto-start on boot:
' 1. Press Win+R, type shell:startup, press Enter
' 2. Create a shortcut to this file in the Startup folder

Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
WshShell.Run "cmd /c venv\Scripts\activate.bat && python -m trinity.main voice", 0, False
