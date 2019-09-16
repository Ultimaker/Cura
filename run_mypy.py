#!/usr/bin/env python
import os
import sys
import subprocess


# A quick Python implementation of unix 'where' command.
def where(exe_name: str, search_path: str = os.getenv("PATH")) -> str:
    if search_path is None:
        search_path = ""
    paths = search_path.split(os.pathsep)
    result = ""
    print("  ->  sys.executable location: %s" % sys.executable)
    sys_exec_dir = os.path.dirname(sys.executable)
    root_dir = os.path.dirname(sys_exec_dir)
    paths += [sys_exec_dir,
              os.path.join(root_dir, "bin"),
              os.path.join(root_dir, "scripts"),
              ]
    paths = set(paths)

    for path in sorted(paths):
        print(" -> Searching %s" % path)
        candidate_path = os.path.join(path, exe_name)
        if os.path.exists(candidate_path):
            result = candidate_path
            break
    return result


def findModules(path):
    result = []
    for entry in os.scandir(path):
        if entry.is_dir() and os.path.exists(os.path.join(path, entry.name, "__init__.py")):
            result.append(entry.name)
    return result


def main():
    # Find Uranium via the PYTHONPATH var
    uraniumUMPath = where("UM", os.getenv("PYTHONPATH"))
    if uraniumUMPath is None:
        uraniumUMPath = os.path.join("..", "Uranium")
    uraniumPath = os.path.dirname(uraniumUMPath)

    mypy_path_parts = [".", os.path.join(".", "plugins"), os.path.join(".", "plugins", "VersionUpgrade"),
                       uraniumPath, os.path.join(uraniumPath, "stubs")]
    if sys.platform == "win32":
        os.putenv("MYPYPATH", ";".join(mypy_path_parts))
    else:
        os.putenv("MYPYPATH", ":".join(mypy_path_parts))

    # Mypy really needs to be run via its Python script otherwise it can't find its data files.
    mypy_exe_name = "mypy.exe" if sys.platform == "win32" else "mypy"
    mypy_exe_dir = where(mypy_exe_name)
    mypy_module = os.path.join(os.path.dirname(mypy_exe_dir), mypy_exe_name)
    print("Found mypy exe path: %s" % mypy_exe_dir)
    print("Found mypy module path: %s" % mypy_module)

    plugins = findModules("plugins")
    plugins.sort()

    mods = ["cura"] + plugins + findModules("plugins/VersionUpgrade")
    result = 0
    for mod in mods:
        print("------------- Checking module {mod}".format(**locals()))
        if sys.platform == "win32":
            result = subprocess.run([mypy_module, "-p", mod, "--ignore-missing-imports"])
        else:
            result = subprocess.run([sys.executable, mypy_module, "-p", mod, "--ignore-missing-imports"])
        if result.returncode != 0:
            print("\nModule {mod} failed checking. :(".format(**locals()))
            result = 1
    else:
        print("\n\nDone checking. All is good.")
    return result


if __name__ == "__main__":
    sys.exit(main())
