@echo off
setlocal
set rambo="drivers/rambo.inf"
set arduino="drivers/arduino.inf"

FOR /F "usebackq" %%A IN ('%rambo%') DO set rambosize=%%~zA
FOR /F "usebackq" %%A IN ('%arduino%') DO set arduinosize=%%~zA
if not "%rambosize%" == "1257" (
   echo RAMBo driver file size is wrong. This could be caused by your local git settings changing the LF line into into CRLF.
   echo Make sure you use the correct INF files
   taskkill.exe /F /IM "makensis.exe"
)
if not "%arduinosize%" == "6460" (
   echo Arduino driver file size is wrong. This could be caused by your local git settings changing the CRLF line into into LF.
   echo Make sure you use the correct INF files
   taskkill.exe /F /IM "makensis.exe"
)
