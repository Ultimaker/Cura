import json
import zipfile
import os
import shutil

root = "./"
pluginjson = json.load(open("./plugin.json"));

package_name = pluginjson["name"].strip().replace(" ", "")
packege_dir = package_name + "/"
plugin_file = package_name + ".curaplugin"

if plugin_file in os.listdir(root):
    os.remove(plugin_file)

if package_name in os.listdir(root):
    shutil.rmtree(package_name)

os.mkdir(package_name)

print("Packaging {} into {}".format(package_name, plugin_file))

with zipfile.ZipFile(plugin_file, "w", zipfile.ZIP_DEFLATED) as output:
    output.write(packege_dir);

    for file in os.listdir(root):
        if file != "PackagePlugin.py" and file[0] != '.' and file != plugin_file and file != package_name:
            output.write(file, packege_dir + file)

if package_name in os.listdir(root):
    shutil.rmtree(package_name)

