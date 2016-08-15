
project(cura)
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

# Macro needed to list all sub-directory of a directory.
# There is no function in cmake as far as I know.
# Found at: http://stackoverflow.com/a/7788165
MACRO(SUBDIRLIST result curdir)
  FILE(GLOB children RELATIVE ${curdir} ${curdir}/*)
  SET(dirlist "")
  FOREACH(child ${children})
    IF(IS_DIRECTORY ${curdir}/${child})
        STRING(REPLACE "/" "" child ${child})
        LIST(APPEND dirlist ${child})
    ENDIF()
  ENDFOREACH()
  SET(${result} ${dirlist})
ENDMACRO()

if(NOT ${URANIUM_SCRIPTS_DIR} STREQUAL "")
    # Extract Strings
    add_custom_target(extract-messages ${URANIUM_SCRIPTS_DIR}/extract-messages ${CMAKE_SOURCE_DIR} cura)

    # Build Translations
    find_package(Gettext)
    if(GETTEXT_FOUND)
        # translations target will convert .po files into .mo and .qm as needed.
        # The files are checked for a _qt suffix and if it is found, converted to
        # qm, otherwise they are converted to .po.
        add_custom_target(translations ALL)
        # copy-translations can be used to copy the built translation files from the
        # build directory to the source resources directory. This is mostly a convenience
        # during development, normally you want to simply use the install target to install
        # the files along side the rest of the application.

        SUBDIRLIST(languages ${CMAKE_SOURCE_DIR}/resources/i18n/)
        foreach(lang ${languages})
            file(GLOB po_files ${CMAKE_SOURCE_DIR}/resources/i18n/${lang}/*.po)
            foreach(po_file ${po_files})
                string(REGEX REPLACE ".*/(.*).po" "${CMAKE_BINARY_DIR}/resources/i18n/${lang}/LC_MESSAGES/\\1.mo" mo_file ${po_file})
                add_custom_command(TARGET translations POST_BUILD COMMAND mkdir ARGS -p ${CMAKE_BINARY_DIR}/resources/i18n/${lang}/LC_MESSAGES/ COMMAND ${GETTEXT_MSGFMT_EXECUTABLE} ARGS ${po_file} -o ${mo_file} -f)
            endforeach()
        endforeach()
        install(DIRECTORY ${CMAKE_BINARY_DIR}/resources
                DESTINATION ${CMAKE_INSTALL_DATADIR}/cura)
    endif()
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
