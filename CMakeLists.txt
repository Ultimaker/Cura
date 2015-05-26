
project(cura)
cmake_minimum_required(VERSION 2.8.12)

set(URANIUM_SCRIPTS_DIR "${CMAKE_SOURCE_DIR}/../uranium/scripts" CACHE DIRECTORY "The location of the scripts directory of the Uranium repository")

if(${URANIUM_SCRIPTS_DIR})
    # Extract Strings
    add_custom_target(extract-messages ${URANIUM_SCRIPTS_DIR}/extract-messages ${CMAKE_SOURCE_DIR} cura)

    # Build Translations
    find_package(Gettext)
    include(${URANIUM_SCRIPTS_DIR}/ECMPoQmTools.cmake)

    if(GETTEXT_FOUND)
        # translations target will convert .po files into .mo and .qm as needed.
        # The files are checked for a _qt suffix and if it is found, converted to
        # qm, otherwise they are converted to .po.
        add_custom_target(translations)
        # copy-translations can be used to copy the built translation files from the
        # build directory to the source resources directory. This is mostly a convenience
        # during development, normally you want to simply use the install target to install
        # the files along side the rest of the application.
        add_custom_target(copy-translations)

        #TODO: Properly install the built files. This should be done after we move the applications out of the Uranium repo.
        set(languages
            en
            x-test
        )
        foreach(lang ${languages})
            file(GLOB po_files resources/i18n/${lang}/*.po)
            foreach(file ${po_files})
                string(REGEX MATCH "qt\\.po$" match "${file}")
                if(match)
                    ecm_process_po_files_as_qm(${lang} PO_FILES ${file})
                else()
                    string(REGEX REPLACE ".*/(.*).po" "${lang}/\\1.mo" mofile ${file})
                    add_custom_command(TARGET translations POST_BUILD COMMAND mkdir ARGS -p ${lang} COMMAND ${GETTEXT_MSGFMT_EXECUTABLE} ARGS ${file} -o ${mofile})
                endif()
            endforeach()

            file(GLOB qm_files ${CMAKE_BINARY_DIR}/${lang}/*.qm)
            file(GLOB mo_files ${CMAKE_BINARY_DIR}/${lang}/*.mo)
            foreach(file ${qm_files} ${mo_files})
                add_custom_command(TARGET copy-translations POST_BUILD COMMAND mkdir ARGS -p ${CMAKE_SOURCE_DIR}/resources/i18n/${lang}/LC_MESSAGES/ COMMAND cp ARGS ${file} ${CMAKE_SOURCE_DIR}/resources/i18n/${lang}/LC_MESSAGES/ COMMENT "Copying ${file}...")
            endforeach()
        endforeach()
    endif()
endif()

include(GNUInstallDirs)
find_package(PythonInterp 3.4.0 REQUIRED)

set(PYTHON_SITE_PACKAGES_DIR ${CMAKE_INSTALL_LIBDIR}/python${PYTHON_VERSION_MAJOR}.${PYTHON_VERSION_MINOR}/site-packages CACHE PATH "Install location of Python package")
install(DIRECTORY resources DESTINATION ${CMAKE_INSTALL_DATADIR}/cura)
install(DIRECTORY plugins DESTINATION ${CMAKE_INSTALL_LIBDIR}/cura)
file(GLOB cura_SRCS cura/*)
install(FILES ${cura_SRCS} DESTINATION ${PYTHON_SITE_PACKAGES_DIR}/cura)
install(FILES cura_app.py DESTINATION ${CMAKE_INSTALL_BINDIR})

