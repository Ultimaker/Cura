project(cura)
cmake_minimum_required(VERSION 3.6)

include(GNUInstallDirs)

list(APPEND CMAKE_MODULE_PATH ${CMAKE_SOURCE_DIR}/cmake)

set(URANIUM_DIR "${CMAKE_SOURCE_DIR}/../Uranium" CACHE DIRECTORY "The location of the Uranium repository")
set(URANIUM_SCRIPTS_DIR "${URANIUM_DIR}/scripts" CACHE DIRECTORY "The location of the scripts directory of the Uranium repository")

# Tests
include(CuraTests)

option(CURA_DEBUGMODE "Enable debug dialog and other debug features" OFF)
if(CURA_DEBUGMODE)
    set(_cura_debugmode "ON")
endif()

set(CURA_APP_NAME "cura" CACHE STRING "Short name of Cura, used for configuration folder")
set(CURA_APP_DISPLAY_NAME "Ultimaker Cura" CACHE STRING "Display name of Cura")
set(CURA_VERSION "master" CACHE STRING "Version name of Cura")
set(CURA_BUILDTYPE "" CACHE STRING "Build type of Cura, eg. 'PPA'")
set(CURA_CLOUD_API_ROOT "" CACHE STRING "Alternative Cura cloud API root")
set(CURA_CLOUD_API_VERSION "" CACHE STRING "Alternative Cura cloud API version")
set(CURA_CLOUD_ACCOUNT_API_ROOT "" CACHE STRING "Alternative Cura cloud account API version")

configure_file(${CMAKE_SOURCE_DIR}/cura.desktop.in ${CMAKE_BINARY_DIR}/cura.desktop @ONLY)

configure_file(cura/CuraVersion.py.in CuraVersion.py @ONLY)


# FIXME: Remove the code for CMake <3.12 once we have switched over completely.
# FindPython3 is a new module since CMake 3.12. It deprecates FindPythonInterp and FindPythonLibs. The FindPython3
# module is copied from the CMake repository here so in CMake <3.12 we can still use it.
if(${CMAKE_VERSION} VERSION_LESS 3.12)
    # Use FindPythonInterp and FindPythonLibs for CMake <3.12
    find_package(PythonInterp 3 REQUIRED)

    set(Python3_EXECUTABLE ${PYTHON_EXECUTABLE})

    set(Python3_VERSION ${PYTHON_VERSION_STRING})
    set(Python3_VERSION_MAJOR ${PYTHON_VERSION_MAJOR})
    set(Python3_VERSION_MINOR ${PYTHON_VERSION_MINOR})
    set(Python3_VERSION_PATCH ${PYTHON_VERSION_PATCH})
else()
    # Use FindPython3 for CMake >=3.12
    find_package(Python3 REQUIRED COMPONENTS Interpreter Development)
endif()


if(NOT ${URANIUM_DIR} STREQUAL "")
    set(CMAKE_MODULE_PATH "${URANIUM_DIR}/cmake")
endif()
if(NOT ${URANIUM_SCRIPTS_DIR} STREQUAL "")
    list(APPEND CMAKE_MODULE_PATH ${URANIUM_DIR}/cmake)
    include(UraniumTranslationTools)
    # Extract Strings
    add_custom_target(extract-messages ${URANIUM_SCRIPTS_DIR}/extract-messages ${CMAKE_SOURCE_DIR} cura)
    # Build Translations
    CREATE_TRANSLATION_TARGETS()
endif()


install(DIRECTORY resources
        DESTINATION ${CMAKE_INSTALL_DATADIR}/cura)
install(DIRECTORY plugins
        DESTINATION lib${LIB_SUFFIX}/cura)

if(NOT APPLE AND NOT WIN32)
    install(FILES cura_app.py
            DESTINATION ${CMAKE_INSTALL_BINDIR}
            PERMISSIONS OWNER_READ OWNER_WRITE OWNER_EXECUTE GROUP_READ GROUP_EXECUTE WORLD_READ WORLD_EXECUTE
            RENAME cura)
    if(EXISTS /etc/debian_version)
        install(DIRECTORY cura
            DESTINATION lib${LIB_SUFFIX}/python${Python3_VERSION_MAJOR}/dist-packages
            FILES_MATCHING PATTERN *.py)
        install(FILES ${CMAKE_BINARY_DIR}/CuraVersion.py
            DESTINATION lib${LIB_SUFFIX}/python${Python3_VERSION_MAJOR}/dist-packages/cura)
    else()
        install(DIRECTORY cura
            DESTINATION lib${LIB_SUFFIX}/python${Python3_VERSION_MAJOR}.${Python3_VERSION_MINOR}/site-packages
            FILES_MATCHING PATTERN *.py)
        install(FILES ${CMAKE_BINARY_DIR}/CuraVersion.py
            DESTINATION lib${LIB_SUFFIX}/python${Python3_VERSION_MAJOR}.${Python3_VERSION_MINOR}/site-packages/cura)
    endif()
    install(FILES ${CMAKE_BINARY_DIR}/cura.desktop
            DESTINATION ${CMAKE_INSTALL_DATADIR}/applications)
    install(FILES ${CMAKE_SOURCE_DIR}/resources/images/cura-icon.png
            DESTINATION ${CMAKE_INSTALL_DATADIR}/icons/hicolor/128x128/apps/)
    install(FILES cura.appdata.xml
            DESTINATION ${CMAKE_INSTALL_DATADIR}/metainfo)
    install(FILES cura.sharedmimeinfo
            DESTINATION ${CMAKE_INSTALL_DATADIR}/mime/packages/
            RENAME cura.xml )
else()
    install(FILES cura_app.py
            DESTINATION ${CMAKE_INSTALL_BINDIR}
            PERMISSIONS OWNER_READ OWNER_WRITE OWNER_EXECUTE GROUP_READ GROUP_EXECUTE WORLD_READ WORLD_EXECUTE)
    install(DIRECTORY cura
            DESTINATION lib${LIB_SUFFIX}/python${Python3_VERSION_MAJOR}.${Python3_VERSION_MINOR}/site-packages
            FILES_MATCHING PATTERN *.py)
    install(FILES ${CMAKE_BINARY_DIR}/CuraVersion.py
            DESTINATION lib${LIB_SUFFIX}/python${Python3_VERSION_MAJOR}.${Python3_VERSION_MINOR}/site-packages/cura)
endif()
