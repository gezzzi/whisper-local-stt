@echo off
cd /d "%~dp0"
call .venv\Scripts\activate.bat
start "" pythonw -m whisper_stt --debug
echo whisper-stt started (log: whisper_stt.log). Check system tray.
