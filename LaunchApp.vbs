Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "pythonw.exe transcribe.py", 0
Set WshShell = Nothing