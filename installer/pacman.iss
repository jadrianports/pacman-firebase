; Inno Setup script for Pac-Man. Compile with: iscc installer\pacman.iss
; Installs to a USER-WRITABLE dir so the in-place auto-updater needs no admin.
#define AppVersion "1.0.0"   ; keep in sync with settings.APP_VERSION

[Setup]
AppId={{8F2C9A41-7B3D-4E6A-9C12-PACMAN000001}
AppName=Pac-Man
AppVersion={#AppVersion}
AppPublisher=jadrianports
DefaultDirName={localappdata}\Pacman
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputBaseFilename=pacman-setup
SetupIconFile=..\assets\icon.ico
UninstallDisplayIcon={app}\pacman.exe
WizardStyle=modern
Compression=lzma2
SolidCompression=yes

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional icons:"

[Files]
Source: "..\dist\pacman\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{autoprograms}\Pac-Man"; Filename: "{app}\pacman.exe"
Name: "{autodesktop}\Pac-Man"; Filename: "{app}\pacman.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\pacman.exe"; Description: "Launch Pac-Man"; Flags: nowait postinstall skipifsilent
