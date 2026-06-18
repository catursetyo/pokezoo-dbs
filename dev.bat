@echo off
echo Starting PokeZOO Development Server...
uvicorn app.main:app --reload
pause
