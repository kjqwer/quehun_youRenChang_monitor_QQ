[Setup]
AppName=雀魂车牌监控
AppVersion=1.0
DefaultDirName={pf}\车牌监控
DefaultGroupName=车牌监控
OutputDir=Output
OutputBaseFilename=车车安装包

[Files]
Source: "dist\车牌监控\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs

[Icons]
Name: "{group}\车牌监控"; Filename: "{app}\车牌监控.exe"
Name: "{commondesktop}\车牌监控"; Filename: "{app}\车牌监控.exe"

[Run]
Filename: "{app}\车牌监控.exe"; Description: "立即运行"; Flags: postinstall nowait 