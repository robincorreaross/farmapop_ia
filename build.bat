@echo off
echo ============================================================
echo   FarmaPop IA - Script de Build
echo ============================================================
echo.

REM Ativa o venv
call venv\Scripts\activate.bat

echo [1/2] Gerando aplicativo cliente (FarmaPop_IA.exe)...
pyinstaller --clean --noconfirm FarmaPop_IA.spec
if errorlevel 1 (
    echo ERRO: falha ao gerar o aplicativo cliente.
    pause
    exit /b 1
)
echo OK - Gerado em: dist\FarmaPop_IA\

echo.
echo [2/2] Gerando ferramenta do desenvolvedor (GeradorLicencas.exe)...
pyinstaller --clean --noconfirm --distpath dist_tools GeradorLicencas.spec
if errorlevel 1 (
    echo ERRO: falha ao gerar o gerador de licencas.
    pause
    exit /b 1
)
echo OK - Gerado em: dist_tools\GeradorLicencas.exe

echo.
echo ============================================================
echo   BUILD CONCLUIDO COM SUCESSO!
echo ============================================================
echo.
echo  Para distribuir ao cliente:
echo    Envie a pasta: dist\FarmaPop_IA\
echo.
echo  Para uso EXCLUSIVO do desenvolvedor:
echo    dist_tools\GeradorLicencas.exe
echo    NAO distribua este arquivo!
echo ============================================================
pause
