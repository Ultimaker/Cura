project(PauseBackendPlugin)
cmake_minimum_required(VERSION 2.8.12)

install(FILES
    __init__.py
    PauseBackend.py
    PauseBackend.qml
    pause.svg
    play.svg
    LICENSE
    README.md
    DESTINATION lib/cura/plugins/PauseBackendPlugin
)
