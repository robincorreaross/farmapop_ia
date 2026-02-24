[Setup]
AppId={{B4C9E2F1-7A3D-4E8B-92F0-1D5A6C8E3B7F}
AppName=FarmaPopIA
AppVersion=1.0.0
DefaultDirName={autopf}\FarmaPopIA
OutputDir=installer
OutputBaseFilename=FarmaPopIA_Setup

[Files]
Source: "dist\FarmaPop_IA\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
