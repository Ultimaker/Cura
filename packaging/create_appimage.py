# Copyright (c) 2022 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import os  # Finding installation directory.
import os.path  # Finding files.
import shutil  # Copying files.
import stat  # For setting file permissions.
import subprocess  # For calling system commands.

dist_path = os.getcwd()  # TODO: Figure out where this is.
appimage_filename = "Ultimaker-Cura_test.AppImage"  # TODO: Get the proper file name.

def build_appimage():
    """
    Creates an AppImage file from the build artefacts created so far.
    """
    copy_metadata_files()

    try:
        os.remove(os.path.join(dist_path, appimage_filename))  # Ensure any old file is removed, if it exists.
    except FileNotFoundError:
        pass  # If it didn't exist, that's even better.

    generate_appimage()

    sign_appimage()

def copy_metadata_files():
    """
    Copy metadata files for the metadata of the AppImage.
    """
    copied_files = {
        "cura-icon_256x256.png": "cura-icon.png",
        "cura.desktop": "cura.desktop",
        "cura.appdata.xml": "cura.appdata.xml",
        "AppRun": "AppRun"
    }

    packaging_dir = os.path.dirname(__file__)
    for source, dest in copied_files.items():
        print("Copying", os.path.join(packaging_dir, source), "to", os.path.join(dist_path, dest))
        shutil.copyfile(os.path.join(packaging_dir, source), os.path.join(dist_path, dest))

    # Ensure that AppRun has the proper permissions: 755 (user reads, writes and executes, group reads and executes, world reads and executes).
    os.chmod(os.path.join(dist_path, "AppRun"), stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)

def generate_appimage():
    appimage_path = os.path.join(dist_path, appimage_filename)
    command = ["appimagetool", "--appimage-extract-and-run", f"{dist_path}/", appimage_path]
    result = subprocess.call(*command)
    if result != 0:
        raise RuntimeError(f"The AppImageTool command returned non-zero: {result}")

def sign_appimage():
    appimage_path = os.path.join(dist_path, appimage_filename)
    command = ["gpg", "--yes", "--armor", "--detach-sig", {appimage_path}]
    result = subprocess.call(*command)
    if result != 0:
        raise RuntimeError(f"The GPG command returned non-zero: {result}")
