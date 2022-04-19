# Copyright (c) 2022 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

project(cura)
cmake_minimum_required(VERSION 3.18)

include(GNUInstallDirs)

list(APPEND CMAKE_MODULE_PATH ${CMAKE_SOURCE_DIR}/cmake)

set(URANIUM_DIR "${CMAKE_SOURCE_DIR}/../Uranium" CACHE PATH "The location of the Uranium repository")
set(URANIUM_SCRIPTS_DIR "${URANIUM_DIR}/scripts" CACHE PATH "The location of the scripts directory of the Uranium repository")

option(CURA_DEBUGMODE "Enable debug dialog and other debug features" OFF)
if(CURA_DEBUGMODE)
    set(_cura_debugmode "ON")
endif()

option(GENERATE_TRANSLATIONS "Should the translations be generated?" ON)

set(CURA_APP_NAME "cura" CACHE STRING "Short name of Cura, used for configuration folder")
set(CURA_APP_DISPLAY_NAME "Ultimaker Cura" CACHE STRING "Display name of Cura")
set(CURA_VERSION "master" CACHE STRING "Version name of Cura")
set(CURA_BUILDTYPE "" CACHE STRING "Build type of Cura, eg. 'PPA'")
set(CURA_CLOUD_API_ROOT "" CACHE STRING "Alternative Cura cloud API root")
set(CURA_CLOUD_API_VERSION "" CACHE STRING "Alternative Cura cloud API version")
set(CURA_CLOUD_ACCOUNT_API_ROOT "" CACHE STRING "Alternative Cura cloud account API version")
set(CURA_MARKETPLACE_ROOT "" CACHE STRING "Alternative Marketplace location")
set(CURA_DIGITAL_FACTORY_URL "" CACHE STRING "Alternative Digital Factory location")

configure_file(${CMAKE_SOURCE_DIR}/com.ultimaker.cura.desktop.in ${CMAKE_BINARY_DIR}/com.ultimaker.cura.desktop @ONLY)

configure_file(cura/CuraVersion.py.in CuraVersion.py @ONLY)

if(NOT DEFINED Python_VERSION)
    set(Python_VERSION
            3.10
            CACHE STRING "Python Version" FORCE)
    message(STATUS "Setting Python version to ${Python_VERSION}. Set Python_VERSION if you want to compile against an other version.")
endif()
if(APPLE)
    set(Python_FIND_FRAMEWORK NEVER)
endif()
find_package(Python ${Python_VERSION} EXACT REQUIRED COMPONENTS Interpreter)
message(STATUS "Linking and building ${project_name} against Python ${Python_VERSION}")
if(NOT DEFINED Python_SITELIB_LOCAL)
    set(Python_SITELIB_LOCAL
            "${Python_SITELIB}"
            CACHE PATH "Local alternative site-package location to install Cura" FORCE)
endif()

# Tests
include(CuraTests)

if(NOT ${URANIUM_DIR} STREQUAL "")
    set(CMAKE_MODULE_PATH "${CMAKE_MODULE_PATH};${URANIUM_DIR}/cmake")
endif()
if(NOT ${URANIUM_SCRIPTS_DIR} STREQUAL "")
    list(APPEND CMAKE_MODULE_PATH ${URANIUM_DIR}/cmake)
    include(UraniumTranslationTools)
    # Extract Strings
    add_custom_target(extract-messages ${URANIUM_SCRIPTS_DIR}/extract-messages ${CMAKE_SOURCE_DIR} cura)
    # Build Translations
    if(${GENERATE_TRANSLATIONS})
        CREATE_TRANSLATION_TARGETS()
    endif()
endif()

install(DIRECTORY resources DESTINATION ${CMAKE_INSTALL_DATADIR}/cura)

include(CuraPluginInstall)

install(FILES cura_app.py DESTINATION ${CMAKE_INSTALL_BINDIR}
        PERMISSIONS OWNER_READ OWNER_WRITE OWNER_EXECUTE GROUP_READ GROUP_EXECUTE WORLD_READ WORLD_EXECUTE)
install(DIRECTORY cura DESTINATION "${Python_SITELIB_LOCAL}")
install(FILES ${CMAKE_BINARY_DIR}/CuraVersion.py DESTINATION "${Python_SITELIB_LOCAL}/cura/")
if(NOT APPLE AND NOT WIN32)
    install(FILES ${CMAKE_BINARY_DIR}/com.ultimaker.cura.desktop
            DESTINATION ${CMAKE_INSTALL_DATADIR}/applications)
    install(FILES ${CMAKE_SOURCE_DIR}/resources/images/cura-icon.png
            DESTINATION ${CMAKE_INSTALL_DATADIR}/icons/hicolor/128x128/apps/)
    install(FILES com.ultimaker.cura.appdata.xml
            DESTINATION ${CMAKE_INSTALL_DATADIR}/metainfo)
    install(FILES cura.sharedmimeinfo
            DESTINATION ${CMAKE_INSTALL_DATADIR}/mime/packages/
            RENAME cura.xml )
endif()
