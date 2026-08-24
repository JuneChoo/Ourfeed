' Launches Ourfeed silently (no console window), for Windows autostart.
' Works from any clone location, the directory is derived from this script's own path.
Set fso = CreateObject("Scripting.FileSystemObject")
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)

Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = scriptDir
WshShell.Run "cmd /c """ & scriptDir & "\start.bat""", 0, False
