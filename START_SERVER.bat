@echo off
color 0A
cls

echo =====================================================
echo    Gemini Report Generator - System Launcher
echo =====================================================
echo.
echo Starting the backend server...
echo.

cd c:\Users\User\Desktop\Gemini

REM Check if Python virtual environment exists
if not exist ".venv" (
    echo Virtual environment not found. Please create it first.
    pause
    exit /b 1
)

REM Start the Flask application
c:/Users/User/Desktop/Gemini/.venv/Scripts/python.exe app.py

if errorlevel 1 (
    echo.
    echo An error occurred. Please check the output above.
    pause
    exit /b 1
)

pause
