; Instalador — Sistema de Busca de Atestados

[Setup]
AppId={{COFRE-BRASUL-2025}}
AppName=Sistema de Busca de Atestados
AppVersion=2.2.0
AppPublisher=Brasul Construtora LTDA
DefaultDirName={autopf}\Brasul\Busca Atestados
DefaultGroupName=Brasul
AllowNoIcons=yes
OutputDir=installer
OutputBaseFilename=Cofre_Brasul_Setup
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
SetupIconFile=assets\icons\iconebrasul2.ico
UninstallDisplayIcon={app}\Cofre_Brasul.exe

[Languages]
Name: "portuguese"; MessagesFile: "compiler:Languages\Portuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar ícone na área de trabalho"; GroupDescription: "Ícones:"

[Files]
Source: "dist\Cofre_Brasul.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "assets\*"; DestDir: "{app}\assets"; Flags: ignoreversion recursesubdirs
Source: "config\*"; DestDir: "{app}\config"; Flags: ignoreversion recursesubdirs
; Modelo de pastas DATA (usuário coloca a base na rede ou local)

[Icons]
Name: "{group}\Busca de Atestados"; Filename: "{app}\Cofre_Brasul.exe"
Name: "{autodesktop}\Busca de Atestados"; Filename: "{app}\Cofre_Brasul.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\Cofre_Brasul.exe"; Description: "Abrir Sistema de Busca de Atestados"; Flags: postinstall nowait skipifsilent

[Registry]
Root: HKCU; Subkey: "Software\Brasul\Cofre Brasul"; ValueType: string; ValueName: "InstallPath"; ValueData: "{app}"; Flags: uninsdeletekey

[Code]
procedure InitializeWizard();
begin
  WizardForm.WelcomeLabel2.Caption :=
    'Instala o Sistema de Busca de Atestados (códigos FDE).' + #13#10 + #13#10 +
    'Planilha: Z:\0 OBRAS\input\Cofre_atestados_brasul.xlsx' + #13#10 +
    'Mapeie a unidade Z: antes de usar. Vários usuários veem alterações em tempo real.';
end;
