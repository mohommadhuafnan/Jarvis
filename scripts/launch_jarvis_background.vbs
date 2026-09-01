Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
rootDir = fso.GetParentFolderName(scriptDir)

pythonwExe = rootDir & "\.venv\Scripts\pythonw.exe"
trayScript = rootDir & "\backend\tray.py"

If Not fso.FileExists(pythonwExe) Then
    pythonwExe = "pythonw.exe"
End If

WshShell.CurrentDirectory = rootDir
WshShell.Run Chr(34) & pythonwExe & Chr(34) & " " & Chr(34) & trayScript & Chr(34), 0, False
Set WshShell = Nothing
Set fso = Nothing
