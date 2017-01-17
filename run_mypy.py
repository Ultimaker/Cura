#!env python
import os
import subprocess

os.putenv("MYPYPATH", r".;.\plugins;..\Uranium_hint\;..\Uranium_hint\stubs\\" )

def findModules(path):
    result = []
    for entry in os.scandir(path):
        if entry.is_dir() and os.path.exists(os.path.join(path, entry.name, "__init__.py")):
            result.append(entry.name)
    return result

plugins = findModules("plugins")
plugins.sort()

mods = ["cura"] + plugins

for mod in mods:
    print("------------- Checking module {mod}".format(**locals()))
    result = subprocess.run(["python", r"c:\python35\Scripts\mypy", "-p", mod])
    if result.returncode != 0:
        print("""
Module {mod} failed checking. :(
""".format(**locals()))
        break
else:
    print("""

Done checking. All is good.
""")
