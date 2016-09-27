project(UM3NetworkPrinting NONE)
cmake_minimum_required(VERSION 2.8.12)

install(FILES
    __init__.py
    DiscoverUM3Action.py
    DiscoverUM3Action.qml
    NetworkPrinterOutputDevice.py
    NetworkPrinterOutputDevicePlugin.py
    UM3InfoComponents.qml
    LICENSE
    README.md
    DESTINATION lib/cura/plugins/UM3NetworkPrinting
)
