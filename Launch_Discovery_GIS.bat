@echo off
title Pre-600 BCE Archaeological Discovery GIS
echo ============================================================================
echo   PRE-600 BCE ARCHAEOLOGICAL DISCOVERY GIS (SUBCONTINENT EDITION)
echo   Opening interactive high-resolution satellite GIS map in your browser...
echo ============================================================================
if exist "%~dp0results\subcontinent\subcontinent_discovery_map.html" (
    start "" "%~dp0results\subcontinent\subcontinent_discovery_map.html"
) else if exist "%~dp0docs\index.html" (
    start "" "%~dp0docs\index.html"
) else (
    echo [ERROR] Map HTML not found!
    pause
)
exit
