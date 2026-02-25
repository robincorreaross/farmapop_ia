; FarmaPop_IA.iss - Script do instalador (Inno Setup 6)

[Setup]
AppId={{B4C9E2F1-7A3D-4E8B-92F0-1D5A6C8E3B7F}
AppName=FarmaPop IA
AppVersion=1.0.5
AppVerName=FarmaPop IA v1.0.5
AppPublisher=Ross Sistemas
AppPublisherURL=https://github.com/robincorreaross/farmapop_ia
DefaultDirName={autopf}\FarmaPop IA
DefaultGroupName=FarmaPop IA
DisableProgramGroupPage=yes
OutputDir=installer
OutputBaseFilename=FarmaPop_IA_Setup_v1.0.5
WizardStyle=modern
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=lowest
AllowNoIcons=yes
UninstallDisplayName=FarmaPop IA
UninstallDisplayIcon={app}\FarmaPop_IA.exe

[Languages]
; Usamos os arquivos .isl locais da pasta installer_meta que foram patcheados (sem BOM)
Name: "english"; MessagesFile: "installer_meta\Default.isl"
Name: "brazilianportuguese"; MessagesFile: "installer_meta\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon";   Description: "Criar atalho na Area de Trabalho"; GroupDescription: "Atalhos:"
Name: "startmenuicon"; Description: "Criar atalho no Menu Iniciar";     GroupDescription: "Atalhos:"

[Files]
Source: "dist\FarmaPop_IA\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autodesktop}\FarmaPop IA";       Filename: "{app}\FarmaPop_IA.exe"; Tasks: desktopicon
Name: "{group}\FarmaPop IA";             Filename: "{app}\FarmaPop_IA.exe"; Tasks: startmenuicon
Name: "{group}\Desinstalar FarmaPop IA"; Filename: "{uninstallexe}";         Tasks: startmenuicon

[Run]
Filename: "{app}\FarmaPop_IA.exe"; Description: "Abrir FarmaPop IA agora"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"
