#define MyAppName "NEW LAXMI MEDICAL & GENERAL STORE"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "NEW LAXMI MEDICAL & GENERAL STORE"
#define MyAppExeName "MedicalStore.exe"

[Setup]
AppId={{7D7F6A7D-6D2E-4A8E-A8D1-1E5F4E7B91A2}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\New Laxmi Medical Store
DefaultGroupName={#MyAppName}
OutputDir=Output
OutputBaseFilename=MedicalStoreSetup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
Uninstallable=yes

[Files]
Source: "dist\MedicalStore.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"
