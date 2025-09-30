@echo off
echo ========================================
echo Building AI Firewall Executable
echo ========================================
echo.

echo Step 1: Installing PyInstaller...
pip install pyinstaller
echo.

echo Step 2: Building executable...
pyinstaller --clean firewall.spec
echo.

echo ========================================
echo Build Complete!
echo ========================================
echo.
echo Your executable is located at:
echo dist\AI_Firewall.exe
echo.
echo IMPORTANT: Run the executable as Administrator!
echo.
pause
