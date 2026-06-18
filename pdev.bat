@echo off
echo Starting PokeZOO Development Server...
python -m uvicorn app.main:app --reload
pause
