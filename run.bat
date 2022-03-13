copy /Y "..\CuraEngine\install_dir\bin\CuraEngine.exe" CuraEngine.exe
cmd /V /C "set PYTHONPATH=!PYTHONPATH!;C:\dev\cura\Uranium && python cura_app.py --debug"
