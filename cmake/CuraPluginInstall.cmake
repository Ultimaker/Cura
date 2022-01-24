# Copyright (c) 2019 Ultimaker B.V.
# CuraPluginInstall.cmake is released under the terms of the LGPLv3 or higher.

#
# This module detects all plugins that need to be installed and adds them using the CMake install() command.
# It detects all plugin folder in the path "plugins/*" where there's a "plugin.json" in it.
#
# Plugins can be configured to NOT BE INSTALLED via the variable "CURA_NO_INSTALL_PLUGINS" as a list of string in the
# form of "a;b;c" or "a,b,c". By default all plugins will be installed.
#

option(PRINT_PLUGIN_LIST "Should the list of plugins that are installed be printed?" ON)

# FIXME: Remove the code for CMake <3.12 once we have switched over completely.
# FindPython3 is a new module since CMake 3.12. It deprecates FindPythonInterp and FindPythonLibs. The FindPython3
# module is copied from the CMake repository here so in CMake <3.12 we can still use it.
if(${CMAKE_VERSION} VERSION_LESS 3.12)
    # Use FindPythonInterp and FindPythonLibs for CMake <3.12
    find_package(PythonInterp 3 REQUIRED)

    set(Python3_EXECUTABLE ${PYTHON_EXECUTABLE})
else()
    # Use FindPython3 for CMake >=3.12
    find_package(Python3 REQUIRED COMPONENTS Interpreter)
endif()

# Options or configuration variables
set(CURA_NO_INSTALL_PLUGINS "" CACHE STRING "A list of plugins that should not be installed, separated with ';' or ','.")

file(GLOB_RECURSE _plugin_json_list ${CMAKE_SOURCE_DIR}/plugins/*/plugin.json)
list(LENGTH _plugin_json_list _plugin_json_list_len)

# Sort the lists alphabetically so we can handle cases like this:
#   - plugins/my_plugin/plugin.json
#   - plugins/my_plugin/my_module/plugin.json
# In this case, only "plugins/my_plugin" should be added via install().
set(_no_install_plugin_list ${CURA_NO_INSTALL_PLUGINS})
# Sanitize the string so the comparison will be case-insensitive.
string(STRIP   "${_no_install_plugin_list}" _no_install_plugin_list)
string(TOLOWER "${_no_install_plugin_list}" _no_install_plugin_list)

# WORKAROUND counterpart of what's in cura-build.
string(REPLACE "," ";" _no_install_plugin_list "${_no_install_plugin_list}")

list(LENGTH _no_install_plugin_list _no_install_plugin_list_len)

if(_no_install_plugin_list_len GREATER 0)
    list(SORT _no_install_plugin_list)
endif()
if(_plugin_json_list_len GREATER 0)
    list(SORT _plugin_json_list)
endif()

# Check all plugin directories and add them via install() if needed.
set(_install_plugin_list "")
foreach(_plugin_json_path ${_plugin_json_list})
    get_filename_component(_plugin_dir ${_plugin_json_path} DIRECTORY)
    file(RELATIVE_PATH _rel_plugin_dir ${CMAKE_CURRENT_SOURCE_DIR} ${_plugin_dir})
    get_filename_component(_plugin_dir_name ${_plugin_dir} NAME)

    # Make plugin name comparison case-insensitive
    string(TOLOWER "${_plugin_dir_name}" _plugin_dir_name_lowercase)

    # Check if this plugin needs to be skipped for installation
    set(_add_plugin ON)  # Indicates if this plugin should be added to the build or not.
    set(_is_no_install_plugin OFF)  # If this plugin will not be added, this indicates if it's because the plugin is
                                    # specified in the NO_INSTALL_PLUGINS list.
    if(_no_install_plugin_list)
        if("${_plugin_dir_name_lowercase}" IN_LIST _no_install_plugin_list)
            set(_add_plugin OFF)
            set(_is_no_install_plugin ON)
        endif()
    endif()

    # Make sure this is not a subdirectory in a plugin that's already in the install list
    if(_add_plugin)
        foreach(_known_install_plugin_dir ${_install_plugin_list})
            if(_plugin_dir MATCHES "${_known_install_plugin_dir}.+")
                set(_add_plugin OFF)
                break()
            endif()
        endforeach()
    endif()

    if(_add_plugin)
        if(${PRINT_PLUGIN_LIST})
            message(STATUS "[+] PLUGIN TO INSTALL: ${_rel_plugin_dir}")
        endif()
        get_filename_component(_rel_plugin_parent_dir ${_rel_plugin_dir} DIRECTORY)
        install(DIRECTORY ${_rel_plugin_dir}
                DESTINATION lib${LIB_SUFFIX}/cura/${_rel_plugin_parent_dir}
                PATTERN "__pycache__" EXCLUDE
                PATTERN "*.qmlc" EXCLUDE
                )
        list(APPEND _install_plugin_list ${_plugin_dir})
    elseif(_is_no_install_plugin)
        if(${PRINT_PLUGIN_LIST})
            message(STATUS "[-] PLUGIN TO REMOVE : ${_rel_plugin_dir}")
        endif()
        execute_process(COMMAND ${Python3_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/cmake/mod_bundled_packages_json.py
                        -d ${CMAKE_CURRENT_SOURCE_DIR}/resources/bundled_packages
                        ${_plugin_dir_name}
                        RESULT_VARIABLE _mod_json_result)
    endif()
endforeach()
