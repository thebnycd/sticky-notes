[Setup]
AppName=Az Note
AppVersion=1.0
AppPublisher=thebnycd
DefaultDirName={autopf}\AzNote
DefaultGroupName=Az Note
OutputBaseFilename=AzNote-Setup
OutputDir=Output
Compression=lzma
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\StickyNotes.exe
PrivilegesRequired=lowest

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[Tasks]
Name: "desktopicon"; Description: "Создать ярлык на рабочем столе"; GroupDescription: "Дополнительно:"
Name: "startup"; Description: "Запускать автоматически при входе в Windows"; GroupDescription: "Дополнительно:"

[Files]
Source: "dist\StickyNotes.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Az Note"; Filename: "{app}\AzNote.exe"
Name: "{group}\Удалить Az Note"; Filename: "{uninstallexe}"
Name: "{commondesktop}\Az Note"; Filename: "{app}\AzNote.exe"; Tasks: desktopicon

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "AzNote"; ValueData: "{app}\AzNote.exe"; Flags: uninsdeletevalue; Tasks: startup

[Run]
Filename: "{app}\AzNote.exe"; Description: "Запустить Az Note сейчас"; Flags: nowait postinstall skipifsilent
