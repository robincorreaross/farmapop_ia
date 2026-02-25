@echo off
echo ============================================================
echo   FarmaPop IA - Build Completo (PyInstaller + Instalador)
echo ============================================================
echo.

REM Ativa o venv
call venv\Scripts\activate.bat

echo [1/3] Compilando o aplicativo com PyInstaller...
pyinstaller --clean --noconfirm FarmaPop_IA.spec
if errorlevel 1 (
    echo ERRO: falha ao gerar o aplicativo.
    pause & exit /b 1
)
echo     OK - dist\FarmaPop_IA\

echo.
echo [2/3] Compilando ferramenta do desenvolvedor...
pyinstaller --clean --noconfirm --distpath dist_tools GeradorLicencas.spec
if errorlevel 1 (
    echo ERRO: falha ao gerar o gerador de licencas.
    pause & exit /b 1
)
echo     OK - dist_tools\GeradorLicencas.exe

echo.
echo [3/3] Gerando instalador com Inno Setup...

REM Procura o compilador do Inno Setup
set ISCC=
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" set ISCC=C:\Program Files (x86)\Inno Setup 6\ISCC.exe
if exist "C:\Program Files\Inno Setup 6\ISCC.exe"       set ISCC=C:\Program Files\Inno Setup 6\ISCC.exe

if "%ISCC%"=="" (
    echo AVISO: Inno Setup nao encontrado.
    echo Instale em: https://jrsoftware.org/isdl.php
    echo Depois execute novamente ou compile manualmente: FarmaPop_IA.iss
    pause & exit /b 0
)

"%ISCC%" FarmaPop_IA.iss
if errorlevel 1 (
    echo ERRO: falha ao gerar o instalador.
    pause & exit /b 1
)

echo.
echo [4/4] Criando pacote ZIP para auto-update...
set ZIP_NAME=FarmaPop_IA.zip
if exist "installer\%ZIP_NAME%" del "installer\%ZIP_NAME%"
powershell -Command "Compress-Archive -Path 'dist\FarmaPop_IA\*' -DestinationPath 'installer\%ZIP_NAME%' -Force"
if errorlevel 1 (
    echo ERRO: falha ao gerar o arquivo ZIP.
    pause & exit /b 1
)
echo     OK - installer\%ZIP_NAME%

echo.
echo ============================================================
echo   BUILD COMPLETO!
echo ============================================================
echo.
echo  Instalador:  installer\FarmaPop_IA_Setup_v1.0.0.exe
echo  Auto-update: installer\FarmaPop_IA.zip
echo  Gerador:     dist_tools\GeradorLicencas.exe (SOMENTE DEV)
echo.
echo  IMPORTANTE: 
echo  1. Envie o .exe para novos clientes.
echo  2. Carregue o .zip no GitHub Releases como 'FarmaPop_IA.zip'
echo     para que os clientes atuais recebam a v%APP_VERSION% automaticamente.
echo ============================================================
pause
