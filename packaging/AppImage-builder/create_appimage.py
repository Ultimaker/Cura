# Copyright (c) 2023 UltiMaker
# Cura is released under the terms of the LGPLv3 or higher.

import argparse
import os
import shutil
import subprocess

from pathlib import Path

from jinja2 import Template


def prepare_workspace(dist_path, appimage_filename):
    """
    Prepare the workspace for building the AppImage.
    :param dist_path: Path to the distribution of Cura created with pyinstaller.
    :param appimage_filename: name of the AppImage file.
    :return:
    """
    if not os.path.exists(dist_path):
        raise RuntimeError(f"The dist_path {dist_path} does not exist.")

    if os.path.exists(os.path.join(dist_path, appimage_filename)):
        os.remove(os.path.join(dist_path, appimage_filename))

    if not os.path.exists("AppDir"):
        shutil.move(dist_path, "AppDir")
    else:
        print(f"AppDir already exists, assuming it is already prepared.")

    copy_files("AppDir")


def build_appimage(dist_path, version, appimage_filename):
    """
    Creates an AppImage file from the build artefacts created so far.
    """
    generate_appimage_builder_config(dist_path, version, appimage_filename)
    create_appimage()
    sign_appimage(appimage_filename)


def generate_appimage_builder_config(dist_path, version, appimage_filename):
    with open(os.path.join(Path(__file__).parent, "AppImageBuilder.yml.jinja"), "r") as appimage_builder_file:
        appimage_builder = appimage_builder_file.read()

    template = Template(appimage_builder)
    appimage_builder = template.render(app_dir = "./AppDir",
                                       icon = "cura-icon.png",
                                       version = version,
                                       arch = "x86_64",
                                       file_name = appimage_filename)

    with open(os.path.join(Path(__file__).parent, "AppImageBuilder.yml"), "w") as appimage_builder_file:
        appimage_builder_file.write(appimage_builder)


def copy_files(dist_path):
    """
    Copy metadata files for the metadata of the AppImage.
    """
    copied_files = {
        os.path.join("..", "icons", "cura-icon.svg"): os.path.join("usr", "share", "icons", "hicolor", "scalable", "apps", "cura-icon.svg"),
        os.path.join("..", "icons", "cura-icon_64x64.png"): os.path.join("usr", "share", "icons", "hicolor", "64x64", "apps", "cura-icon.png"),
        os.path.join("..", "icons", "cura-icon_128x128.png"): os.path.join("usr", "share", "icons", "hicolor", "128x128", "apps", "cura-icon.png"),
        os.path.join("..", "icons", "cura-icon_256x256.png"): os.path.join("usr", "share", "icons", "hicolor", "256x256", "apps", "cura-icon.png"),
        os.path.join("..", "icons", "cura-icon_256x256.png"): "cura-icon.png",
    }

    # TODO: openssl.cnf ???

    packaging_dir = os.path.dirname(__file__)
    for source, dest in copied_files.items():
        dest_file_path = os.path.join(dist_path, dest)
        os.makedirs(os.path.dirname(dest_file_path), exist_ok = True)
        shutil.copyfile(os.path.join(packaging_dir, source), dest_file_path)


def create_appimage():
    appimagetool = os.getenv("APPIMAGEBUILDER_LOCATION", "appimage-builder-x86_64.AppImage")
    command = [appimagetool, "--recipe", os.path.join(Path(__file__).parent, "AppImageBuilder.yml"), "--skip-test"]
    result = subprocess.call(command)
    if result != 0:
        raise RuntimeError(f"The AppImageTool command returned non-zero: {result}")


def sign_appimage(appimage_filename):
    command = ["gpg", "--yes", "--armor", "--detach-sig", appimage_filename]
    result = subprocess.call(command)
    if result != 0:
        raise RuntimeError(f"The GPG command returned non-zero: {result}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description = "Create AppImages of Cura.")
    parser.add_argument("dist_path", type = str, help = "Path to where PyInstaller installed the distribution of Cura.")
    parser.add_argument("version", type = str, help = "Full version number of Cura (e.g. '5.1.0-beta')")
    parser.add_argument("filename", type = str, help = "Filename of the AppImage (e.g. 'UltiMaker-Cura-5.1.0-beta-Linux-X64.AppImage')")
    args = parser.parse_args()
    prepare_workspace(args.dist_path, args.filename)
    build_appimage(args.dist_path, args.version, args.filename)
