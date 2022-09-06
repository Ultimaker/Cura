# Copyright (c) 2022 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

# NOTE: This is only being used for translation scripts.

# For MSVC flags, will be ignored on non-Windows OS's and this project in general. Only needed for cura-build-environment.
cmake_policy(SET CMP0091 NEW)
project(cura)
cmake_minimum_required(VERSION 3.18)

include(GNUInstallDirs)

list(APPEND CMAKE_MODULE_PATH ${CMAKE_SOURCE_DIR}/cmake)

set(URANIUM_DIR "${CMAKE_SOURCE_DIR}/../Uranium" CACHE PATH "The location of the Uranium repository")
set(URANIUM_SCRIPTS_DIR "${URANIUM_DIR}/scripts" CACHE PATH "The location of the scripts directory of the Uranium repository")

option(GENERATE_TRANSLATIONS "Should the translations be generated?" ON)

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