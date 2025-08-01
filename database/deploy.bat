REM Quick deployment script for Windows systems
@echo off
setlocal

echo 🚀 Energy Certificate Database Deployment
echo ========================================

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is required but not installed
    exit /b 1
)

REM Check if required environment variable is set
if "%DATABASE_CONNECTION_STRING%"=="" (
    echo ❌ DATABASE_CONNECTION_STRING environment variable is not set
    echo    Example: set DATABASE_CONNECTION_STRING=Driver={ODBC Driver 17 for SQL Server};Server=server;Database=db;UID=user;PWD=pass
    exit /b 1
)

REM Navigate to database directory
cd /d "%~dp0"
echo 📁 Current directory: %CD%

REM Install Python dependencies if requirements.txt exists
if exist "requirements.txt" (
    echo 📦 Installing Python dependencies...
    pip install -r requirements.txt
)

echo 🔍 Validating database connection...
python scripts\validate.py
if errorlevel 1 (
    echo ❌ Database connection validation failed
    exit /b 1
)
echo ✅ Database connection validated

echo 🚀 Starting database deployment...
python scripts\deploy.py
if errorlevel 1 (
    echo ❌ Database deployment failed
    exit /b 1
)

echo ✅ Database deployment completed successfully!
echo 📊 Running final validation...
python scripts\validate.py

echo 🎉 All done! Database is ready to use.
pause
