#define MyAppName "Logitech C920 LED Control"
#define MyAppVersion "0.4.0"
[Setup]
AppId={{DB735D7B-BB4D-496C-8D9E-0A97910CC0A3}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
DefaultDirName={localappdata}\Programs\C920LEDControl
DefaultGroupName={#MyAppName}
OutputDir=..\release
OutputBaseFilename=C920_LED_Control_Setup_Windows
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=lowest
WizardStyle=modern
UninstallDisplayIcon={app}\C920LEDControl.exe
[Files]
Source: "..\dist\C920LEDControl\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
[Icons]
Name: "{group}\Logitech C920 LED Control"; Filename: "{app}\C920LEDControl.exe"
Name: "{autodesktop}\Logitech C920 LED Control"; Filename: "{app}\C920LEDControl.exe"; Tasks: desktopicon
[Tasks]
Name: "desktopicon"; Description: "Criar atalho na area de trabalho"; GroupDescription: "Atalhos adicionais:"
[Run]
Filename: "{app}\C920LEDControl.exe"; Description: "Abrir Logitech C920 LED Control"; Flags: nowait postinstall skipifsilent
