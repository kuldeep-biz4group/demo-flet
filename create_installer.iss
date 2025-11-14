; ----------------------------------------------------------
; Clarikey Report Generator - Windows Installer
; ----------------------------------------------------------

#define MyAppName "Clarikey Report Generator"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Clarikey Analytics Pvt Ltd"
#define MyAppURL "https://clarikey.com"
#define MyAppExeName "ReportGenerator.exe"

[Setup]
AppId={{E2F1A9B1-6C44-4D2C-92AB-87FA32C88A11}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputBaseFilename=Clarikey_Report_Generator_Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
SetupIconFile="app\assets\icon.ico"

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; \
Description: "Create a desktop shortcut"; \
GroupDescription: "Additional icons:"; \
Flags: unchecked

[Files]
Source: "dist\ReportGenerator_Package\*"; \
DestDir: "{app}"; \
Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Start Menu Shortcut
Name: "{autoprograms}\{#MyAppName}"; \
Filename: "{app}\{#MyAppExeName}"

; Desktop Shortcut
Name: "{autodesktop}\{#MyAppName}"; \
Filename: "{app}\{#MyAppExeName}"; \
Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; \
Description: "Launch Clarikey Report Generator now"; \
Flags: nowait postinstall skipifsilent
