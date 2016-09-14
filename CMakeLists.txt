
project(cura NONE)
cmake_minimum_required(VERSION 2.8.12)

include(GNUInstallDirs)

set(URANIUM_SCRIPTS_DIR "${CMAKE_SOURCE_DIR}/../uranium/scripts" CACHE DIRECTORY "The location of the scripts directory of the Uranium repository")

# Tests
# Note that we use exit 0 here to not mark the build as a failure on test failure
add_custom_target(tests)
add_custom_command(TARGET tests POST_BUILD COMMAND "PYTHONPATH=${CMAKE_SOURCE_DIR}/../Uranium/:${CMAKE_SOURCE_DIR}" ${PYTHON_EXECUTABLE} -m pytest -r a --junitxml=${CMAKE_BINARY_DIR}/junit.xml ${CMAKE_SOURCE_DIR} || exit 0)


set(CURA_VERSION "master" CACHE STRING "Version name of Cura")
set(CURA_BUILDTYPE "" CACHE STRING "Build type of Cura, eg. 'PPA'")
configure_file(${CMAKE_SOURCE_DIR}/cura.desktop.in ${CMAKE_BINARY_DIR}/cura.desktop @ONLY)
configure_file(cura/CuraVersion.py.in CuraVersion.py @ONLY)

if(NOT ${URANIUM_SCRIPTS_DIR} STREQUAL "")
    include(UraniumTranslationTools)
    # Extract Strings
    add_custom_target(extract-messages ${URANIUM_SCRIPTS_DIR}/extract-messages ${CMAKE_SOURCE_DIR} cura)
    # Build Translations
    CREATE_TRANSLATION_TARGETS()
endif()

find_package(PythonInterp 3.4.0 REQUIRED)

install(DIRECTORY resources
        DESTINATION ${CMAKE_INSTALL_DATADIR}/cura)
install(DIRECTORY plugins
        DESTINATION lib/cura)
if(NOT APPLE AND NOT WIN32)
    install(FILES cura_app.py
            DESTINATION ${CMAKE_INSTALL_BINDIR}
            PERMISSIONS OWNER_READ OWNER_WRITE OWNER_EXECUTE GROUP_READ GROUP_EXECUTE WORLD_READ WORLD_EXECUTE
            RENAME cura)
    install(DIRECTORY cura
            DESTINATION lib/python${PYTHON_VERSION_MAJOR}/dist-packages
            FILES_MATCHING PATTERN *.py)
    install(FILES ${CMAKE_BINARY_DIR}/CuraVersion.py
            DESTINATION lib/python${PYTHON_VERSION_MAJOR}/dist-packages/cura)
    install(FILES ${CMAKE_BINARY_DIR}/cura.desktop
            DESTINATION ${CMAKE_INSTALL_DATADIR}/applications)
    install(FILES cura.sharedmimeinfo
            DESTINATION ${CMAKE_INSTALL_DATADIR}/mime/packages/
            RENAME cura.xml )
else()
    install(FILES cura_app.py
            DESTINATION ${CMAKE_INSTALL_BINDIR}
            PERMISSIONS OWNER_READ OWNER_WRITE OWNER_EXECUTE GROUP_READ GROUP_EXECUTE WORLD_READ WORLD_EXECUTE)
    install(DIRECTORY cura
            DESTINATION lib/python${PYTHON_VERSION_MAJOR}.${PYTHON_VERSION_MINOR}/site-packages
            FILES_MATCHING PATTERN *.py)
    install(FILES ${CMAKE_BINARY_DIR}/CuraVersion.py
            DESTINATION lib/python${PYTHON_VERSION_MAJOR}.${PYTHON_VERSION_MINOR}/site-packages/cura)
endif()

include(CPackConfig.cmake)
