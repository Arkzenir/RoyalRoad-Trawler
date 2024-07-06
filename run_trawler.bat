@echo off
setlocal

:: Prompt the user for the starting URL
set /p START_URL="Enter the starting page URL (leave blank to use default from config.json): "

:: Check if the user provided a URL
if "%START_URL%"=="" (
    :: Run the Python script without the URL argument
    py trawler.py
) else (
    :: Run the Python script with the provided URL
    py trawler.py %START_URL%
)

endlocal
pause
