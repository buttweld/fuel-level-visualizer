@echo off
cd /d %~dp0
set PYTHONPATH=src
call .venv\Scripts\activate.bat
python -m visualizer.main %*
