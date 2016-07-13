project(MachineSettingsAction)
cmake_minimum_required(VERSION 2.8.12)

install(FILES
    __init__.py
    MachineSettingsAction.py
    MachineSettingsAction.qml
    LICENSE
    README.md
    DESTINATION lib/cura/plugins/MachineSettingsAction
)
