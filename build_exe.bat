@echo off
REM Gera o executavel do Sistema de Rodizio.
REM Uso: da um duplo-clique neste arquivo, ou rode "build_exe.bat" no terminal,
REM sempre estando dentro da pasta do projeto.

echo Instalando PyInstaller (se ainda nao estiver instalado)...
python -m pip install pyinstaller --quiet

echo.
echo Limpando builds anteriores...
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul

echo.
echo Gerando o executavel...
python -m PyInstaller ^
    --onefile ^
    --windowed ^
    --name "SistemaRodizio" ^
    --icon "assets\icone_rotacao.ico" ^
    --add-data "assets;assets" ^
    --collect-data customtkinter ^
    main.py

echo.
echo ==========================================================
echo Pronto! O executavel esta em: dist\SistemaRodizio.exe
echo ==========================================================
pause