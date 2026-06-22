@echo off
setlocal enabledelayedexpansion

echo Deshaciendo organizacion de carpetas...
echo.

:: Mover todos los archivos de subcarpetas al directorio raiz
for /r %%F in (*) do (
    if not "%%~dpF"=="%CD%\" (
        move "%%F" "%CD%\%%~nxF" >nul 2>&1
        if !errorlevel! equ 0 (
            echo Movido: %%~nxF
        ) else (
            echo Error moviendo: %%~nxF
        )
    )
)

:: Eliminar todas las subcarpetas vacias
for /f "delims=" %%D in ('dir /ad /b /s ^| sort /r') do (
    rd "%%D" >nul 2>&1
    if !errorlevel! equ 0 (
        echo Carpeta eliminada: %%D
    )
)

echo.
echo Proceso completado. Todos los archivos estan en la carpeta raiz.
pause