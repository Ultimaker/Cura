# Copyright (c) 2022 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import argparse  # Command line arguments parsing and help.
from jinja2 import Template
import os  # Finding installation directory.
import os.path  # Finding files.
import shutil  # Copying files.
import stat  # For setting file permissions.
import subprocess  # For calling system commands.

def build_appimage(dist_path, version):
    """
    Creates an AppImage file from the build artefacts created so far.
    """
    copy_metadata_files(dist_path, version)

    appimage_filename = f"Ultimaker-Cura_{version}.AppImage"
    try:
        os.remove(os.path.join(dist_path, appimage_filename))  # Ensure any old file is removed, if it exists.
    except FileNotFoundError:
        pass  # If it didn't exist, that's even better.

    generate_appimage(dist_path, appimage_filename)

    sign_appimage(dist_path, appimage_filename)

def copy_metadata_files(dist_path, version):
    """
    Copy metadata files for the metadata of the AppImage.
    """
    copied_files = {
        os.path.join("..", "icons", "cura-icon_256x256.png"): "cura-icon.png",
        "cura.appdata.xml": "cura.appdata.xml",
        "AppRun": "AppRun"
    }

    packaging_dir = os.path.dirname(__file__)
    for source, dest in copied_files.items():
        print("Copying", os.path.join(packaging_dir, source), "to", os.path.join(dist_path, dest))
        shutil.copyfile(os.path.join(packaging_dir, source), os.path.join(dist_path, dest))

    # Ensure that AppRun has the proper permissions: 755 (user reads, writes and executes, group reads and executes, world reads and executes).
    print("Changing permissions for AppRun")
    os.chmod(os.path.join(dist_path, "AppRun"), stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)

    # Provision the Desktop file with the correct version number.
    template_path = os.path.join(packaging_dir, "cura.desktop.jinja")
    desktop_path = os.path.join(dist_path, "cura.desktop")
    print("Provisioning desktop file from", template_path, "to", desktop_path)
    with open(template_path, "r") as f:
        desktop_file = Template(f.read())
    with open(desktop_path, "w") as f:
        f.write(desktop_file.render(cura_version = version))

def generate_appimage(dist_path, appimage_filename):
    appimage_path = os.path.join(dist_path, appimage_filename)
    appimagetool = os.getenv("APPIMAGETOOL_LOCATION", "appimagetool")
    command = [appimagetool, "--appimage-extract-and-run", f"{dist_path}/", appimage_path]
    result = subprocess.call(command)
    if result != 0:
        raise RuntimeError(f"The AppImageTool command returned non-zero: {result}")

def sign_appimage(dist_path, appimage_filename):
    appimage_path = os.path.join(dist_path, appimage_filename)
    command = ["gpg", "--yes", "--armor", "--detach-sig", appimage_path]
    result = subprocess.call(command)
    if result != 0:
        raise RuntimeError(f"The GPG command returned non-zero: {result}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description = "Create AppImages of Cura.")
    parser.add_argument("dist_path", type=str, help="Path to where PyInstaller installed the distribution of Cura.")
    parser.add_argument("version", type=str, help="Full version number of Cura (e.g. '5.1.0-beta')")
    args = parser.parse_args()
    build_appimage(args.dist_path, args.version)
