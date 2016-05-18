project(JediWifiPrintingPlugin)
cmake_minimum_required(VERSION 2.8.12)

install(FILES
    __init__.py
    HttpUploadDataStream.py
    NetworkPrinterOutputDevice.py
    NetworkPrinterOutputDevicePlugin.py
    LICENSE
    README.md
    DESTINATION lib/cura/plugins/JediWifiPrintingPlugin
)
