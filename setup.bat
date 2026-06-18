@echo off
echo =========================================
echo  PokeZOO Setup for Windows
echo =========================================
echo.

echo [1/4] Installing Python dependencies...
pip install -r requirements.txt
echo.

echo [2/4] Creating database and running migration...
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS pokezoo;"
mysql -u root -p pokezoo < database\schema.sql
echo.

echo [3/4] Seeding MySQL dummy data...
mysql -u root -p pokezoo < database\seed.sql
echo.

echo [4/4] Seeding MongoDB dummy data...
mongosh pokezoo database\mongo_seed.js
echo.

echo =========================================
echo  Setup Complete! 
echo  You can now run 'dev.bat' to start the server.
echo =========================================
pause
