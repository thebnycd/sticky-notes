[Setup]
AppName=Sticky Notes
AppVersion=1.0
AppPublisher=thebnycd
DefaultDirName={autopf}\StickyNotes
DefaultGroupName=Sticky Notes
OutputBaseFilename=StickyNotes-Setup
OutputDir=Output
Compression=lzma
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\StickyNotes.exe
PrivilegesRequired=lowest

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[Tasks]
Name: "desktopicon"; Description: "Создать ярлык на рабочем столе"; GroupDescription: "Дополнительно:"; Flags: checked
Name: "startup"; Description: "Запускать автоматически при входе в Windows"; GroupDescription: "Дополнительно:"; Flags: checked

[Files]
Source: "dist\StickyNotes.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Sticky Notes"; Filename: "{app}\StickyNotes.exe"
Name: "{group}\Удалить Sticky Notes"; Filename: "{uninstallexe}"
Name: "{commondesktop}\Sticky Notes"; Filename: "{app}\StickyNotes.exe"; Tasks: desktopicon

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "StickyNotes"; ValueData: "{app}\StickyNotes.exe"; Flags: uninsdeletevalue; Tasks: startup

[Run]
Filename: "{app}\StickyNotes.exe"; Description: "Запустить Sticky Notes сейчас"; Flags: nowait postinstall skipifsilent
