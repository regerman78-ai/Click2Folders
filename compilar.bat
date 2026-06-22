@echo off
chcp 65001 >nul
echo.
echo ================================================
echo     COMPILANDO CLICK2FOLDERS - VERSIÓN PREMIUM
echo ================================================
echo.

:: Verifica que pyinstaller esté instalado
python -c "import PyInstaller" 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] PyInstaller no está instalado.
    echo         Ejecuta: pip install pyinstaller
    pause
    exit /b 1
)

:: Verifica que el .spec exista
if not exist "click2folders.spec" (
    echo [ERROR] No se encontró click2folders.spec
    pause
    exit /b 1
)

:: Compila con el .spec
echo [INFO] Iniciando compilación con click2folders.spec...
pyinstaller click2folders.spec

if %errorlevel% equ 0 (
    echo.
    echo [ÉXITO] ¡Compilación completada!
    echo         El ejecutable está en: dist\Click2Folders.exe
    echo.
    echo Presiona cualquier tecla para abrir la carpeta...
    pause >nul
    start "" "dist"
) else (
    echo.
    echo [ERROR] Falló la compilación. Revisa el log arriba.
    pause
)

exit /b 0