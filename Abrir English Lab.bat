@echo off
REM Doble clic aqui para abrir English Lab en el navegador.
REM Para cerrar la app, cierra esta ventana negra.
cd /d "%~dp0"
"%LOCALAPPDATA%\Programs\Python\Python314\python.exe" -m streamlit run app.py --browser.gatherUsageStats false
pause
