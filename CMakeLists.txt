project(JediWifiPrintingPlugin)
cmake_minimum_required(VERSION 2.8.12)

install(FILES
    __init__.py
    DiscoverUM3Action.py
    DiscoverUM3Action.qml
    NetworkPrinterOutputDevice.py
    NetworkPrinterOutputDevicePlugin.py
    LICENSE
    README.md
    DESTINATION lib/cura/plugins/JediWifiPrintingPlugin
)
