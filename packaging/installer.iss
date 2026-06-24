[Setup]
AppName=PDF Presenter
AppVersion=1.0
DefaultDirName={autopf}\PDF Presenter
OutputDir=dist
OutputBaseFilename=PDF-Presenter-Setup
Compression=lzma
SolidCompression=yes

[Files]
Source: "..\dist\PDF Presenter\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs

[Icons]
Name: "{autodesktop}\PDF Presenter"; Filename: "{app}\PDF Presenter.exe"
Name: "{group}\PDF Presenter"; Filename: "{app}\PDF Presenter.exe"

[Run]
Filename: "{app}\PDF Presenter.exe"; Description: "Lancer PDF Presenter"; Flags: nowait postinstall skipifsilent
