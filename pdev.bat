@echo off
echo Starting PokeZOO Development Server...
python3 -m uvicorn app.main:app --reload
pause
