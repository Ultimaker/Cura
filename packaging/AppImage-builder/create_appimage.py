# Copyright (c) 2023 UltiMaker
# Cura is released under the terms of the LGPLv3 or higher.


import argparse  # Command line arguments parsing and help.
from jinja2 import Template
import os  # Finding installation directory.
import os.path  # Finding files.
import shutil  # Copying files.
import stat  # For setting file permissions.
import subprocess  # For calling system commands.

def build_appimage(dist_path, version, appimage_filename):
    """
    Creates an AppImage file from the build artefacts created so far.
    """
    generate_appimage_builder_config(dist_path, version, appimage_filename)
    generate_appimage_entrypoint(dist_path)
    copy_files(dist_path)

    try:
        os.remove(os.path.join(dist_path, appimage_filename))  # Ensure any old file is removed, if it exists.
    except FileNotFoundError:
        pass  # If it didn't exist, that's even better.
    create_appimage(dist_path, appimage_filename)
    sign_appimage(dist_path, appimage_filename)


def generate_appimage_builder_config(dist_path, version, appimage_filename):
    with open(os.path.join(dist_path, "AppImageBuilder.yml.jinja"), "r") as appimage_builder_file:
        appimage_builder = appimage_builder_file.read()

    template = Template(appimage_builder)
    appimage_builder = template.render(app_dir = dist_path,
                                       icon = os.path.join("..", "icons", "cura-icon_256x256.png"),
                                       version = version,
                                       arch = "x86_64",
                                       file_name = appimage_filename)

    with open(os.path.join(dist_path, "AppImageBuilder.yml"), "w") as appimage_builder_file:
        appimage_builder_file.write(appimage_builder)


def generate_appimage_entrypoint(dist_path):
    with open(os.path.join(dist_path, "entrypoint.sh.jinja"), "r") as entrypoint_file:
        entrypoint = entrypoint_file.read()

    template = Template(entrypoint)
    entrypoint = template.render(executable = "UltiMaker-Cura")

    with open(os.path.join(dist_path, "entrypoint.sh"), "w") as entrypoint_file:
        entrypoint_file.write(entrypoint)

def copy_files(dist_path):
    """
    Copy metadata files for the metadata of the AppImage.
    """
    copied_files = {
        os.path.join("..", "icons", "cura-icon.svg"):         os.path.join("usr", "share", "icons", "hicolor", "scalable", "apps", "cura-icon.svg"),
        os.path.join("..", "icons", "cura-icon_64x64.png"):   os.path.join("usr", "share", "icons", "hicolor", "64x64", "apps", "cura-icon.png"),
        os.path.join("..", "icons", "cura-icon_128x128.png"): os.path.join("usr", "share", "icons", "hicolor", "128x128", "apps", "cura-icon.png"),
        os.path.join("..", "icons", "cura-icon_256x256.png"): os.path.join("usr", "share", "icons", "hicolor", "256x256", "apps", "cura-icon.png"),
        os.path.join("..", "icons", "cura-icon_256x256.png"): "cura-icon.png",
        "entrypoint.sh": "entrypoint.sh"
    }

    # TODO: openssl.cnf ???

    packaging_dir = os.path.dirname(__file__)
    for source, dest in copied_files.items():
        dest_file_path = os.path.join(dist_path, dest)
        os.makedirs(os.path.dirname(dest_file_path), exist_ok=True)
        shutil.copyfile(os.path.join(packaging_dir, source), dest_file_path)

    # Ensure that entrypoint.sh has the proper permissions: 755 (user reads, writes and executes, group reads and executes, world reads and executes).
    os.chmod(os.path.join(dist_path, "entrypoint.sh"), stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)

def create_appimage(dist_path, appimage_filename):
    appimage_path = os.path.join(dist_path, "..", appimage_filename)
    appimagetool = os.getenv("APPIMAGETOOL_LOCATION", "appimagetool")
    command = [appimagetool, "--appimage-extract-and-run", f"{dist_path}/", appimage_path]
    result = subprocess.call(command)
    if result != 0:
        raise RuntimeError(f"The AppImageTool command returned non-zero: {result}")

def sign_appimage(dist_path, appimage_filename):
    appimage_path = os.path.join(dist_path, "..", appimage_filename)
    command = ["gpg", "--yes", "--armor", "--detach-sig", appimage_path]
    result = subprocess.call(command)
    if result != 0:
        raise RuntimeError(f"The GPG command returned non-zero: {result}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description = "Create AppImages of Cura.")
    parser.add_argument("dist_path", type=str, help="Path to where PyInstaller installed the distribution of Cura.")
    parser.add_argument("version", type=str, help="Full version number of Cura (e.g. '5.1.0-beta')")
    parser.add_argument("filename", type = str, help = "Filename of the AppImage (e.g. 'UltiMaker-Cura-5.1.0-beta-Linux-X64.AppImage')")
    args = parser.parse_args()
    build_appimage(args.dist_path, args.version, args.filename)
