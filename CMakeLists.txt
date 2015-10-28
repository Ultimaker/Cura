
project(cura)
cmake_minimum_required(VERSION 2.8.12)

include(GNUInstallDirs)

set(URANIUM_SCRIPTS_DIR "${CMAKE_SOURCE_DIR}/../uranium/scripts" CACHE DIRECTORY "The location of the scripts directory of the Uranium repository")

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
        add_custom_target(copy-translations)

        #TODO: Properly install the built files. This should be done after we move the applications out of the Uranium repo.
        set(languages
            en
            x-test
            ru
            fr
            de
            it
            es
            fi
            pl
            cs
            bg
        )
        foreach(lang ${languages})
            file(GLOB po_files resources/i18n/${lang}/*.po)
            foreach(file ${po_files})
                string(REGEX REPLACE ".*/(.*).po" "${lang}/\\1.mo" mofile ${file})
                add_custom_command(TARGET translations POST_BUILD COMMAND mkdir ARGS -p ${lang} COMMAND ${GETTEXT_MSGFMT_EXECUTABLE} ARGS ${file} -o ${mofile})
            endforeach()

            file(GLOB mo_files ${CMAKE_BINARY_DIR}/${lang}/*.mo)
            foreach(file ${mo_files})
                add_custom_command(TARGET copy-translations POST_BUILD COMMAND mkdir ARGS -p ${CMAKE_SOURCE_DIR}/resources/i18n/${lang}/LC_MESSAGES/ COMMAND cp ARGS ${file} ${CMAKE_SOURCE_DIR}/resources/i18n/${lang}/LC_MESSAGES/ COMMENT "Copying ${file}...")
            endforeach()

            install(FILES ${mo_files} DESTINATION ${CMAKE_INSTALL_DATADIR}/uranium/resources/i18n/${lang}/LC_MESSAGES/)
        endforeach()
    endif()
endif()

find_package(PythonInterp 3.4.0 REQUIRED)

install(DIRECTORY resources DESTINATION ${CMAKE_INSTALL_DATADIR}/cura)
install(DIRECTORY plugins DESTINATION lib/cura)
install(FILES cura_app.py DESTINATION ${CMAKE_INSTALL_BINDIR} PERMISSIONS OWNER_READ OWNER_WRITE OWNER_EXECUTE GROUP_READ GROUP_EXECUTE WORLD_READ WORLD_EXECUTE)
if(NOT APPLE AND NOT WIN32)
    install(DIRECTORY cura DESTINATION lib/python${PYTHON_VERSION_MAJOR}/dist-packages)
    install(FILES cura.desktop DESTINATION ${CMAKE_INSTALL_DATADIR}/applications)
else()
    install(DIRECTORY cura DESTINATION lib/python${PYTHON_VERSION_MAJOR}.${PYTHON_VERSION_MINOR}/site-packages)
endif()

include(CPackConfig.cmake)
