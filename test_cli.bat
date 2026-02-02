@echo off
echo ============================================================
echo Testing CLI Entry Points
echo ============================================================
echo.

echo Test 1: Direct execution of __main__.py
python __main__.py --help
echo.

echo Test 2: Module execution (requires installation)
echo Note: Run 'pip install -e .' first
python -m behavioral_health --help
echo.

echo Test 3: Check if Click is installed
python -c "import click; print('Click version:', click.__version__)"
echo.

echo ============================================================
echo Test complete!
echo ============================================================
pause
