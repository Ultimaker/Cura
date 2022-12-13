# Copyright (c) 2022 UltiMaker
# Cura is released under the terms of the LGPLv3 or higher.


import os
import argparse  # Command line arguments parsing and help.
import subprocess

ULTIMAKER_CURA_DOMAIN = os.environ.get("ULTIMAKER_CURA_DOMAIN", "nl.ultimaker.cura")


def build_dmg(source_path: str, dist_path: str, filename: str) -> None:
    create_dmg_executable = os.environ.get("CREATE_DMG_EXECUTABLE", "create-dmg")

    arguments = [create_dmg_executable,
                 "--window-pos", "640", "360",
                 "--window-size", "690", "503",
                 "--app-drop-link", "520", "272",
                 "--volicon", f"{source_path}/packaging/icons/VolumeIcons_Cura.icns",
                 "--icon-size", "90",
                 "--icon", "UltiMaker-Cura.app", "169", "272",
                 "--eula", f"{source_path}/packaging/cura_license.txt",
                 "--background", f"{source_path}/packaging/dmg/cura_background_dmg.png",
                 f"{dist_path}/{filename}",
                 f"{dist_path}/UltiMaker-Cura.app"]

    subprocess.run(arguments)


def sign(dist_path: str, filename: str) -> None:
    codesign_executable = os.environ.get("CODESIGN", "codesign")
    codesign_identity = os.environ.get("CODESIGN_IDENTITY")

    arguments = [codesign_executable,
                 "-s", codesign_identity,
                 "--timestamp",
                 "-i", f"{ULTIMAKER_CURA_DOMAIN}.dmg",  # TODO: check if this really should have the extra dmg. We seem to be doing this also in the old Rundeck scripts
                 f"{dist_path}/{filename}"]

    subprocess.run(arguments)


def notarize(dist_path: str, filename: str) -> None:
    notarize_user = os.environ.get("MAC_NOTARIZE_USER")
    notarize_password = os.environ.get("MAC_NOTARIZE_PASS")
    altool_executable = os.environ.get("ALTOOL_EXECUTABLE", "altool")

    arguments = [
        "xcrun", altool_executable,
        "--notarize-app",
        "--primary-bundle-id", ULTIMAKER_CURA_DOMAIN,
        "--username", notarize_user,
        "--password", notarize_password,
        "--file", f"{dist_path}/{filename}"
    ]

    subprocess.run(arguments)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description = "Create dmg of Cura.")
    parser.add_argument("source_path", type=str, help="Path to Conan install Cura folder.")
    parser.add_argument("dist_path", type=str, help="Path to Pyinstaller dist folder")
    parser.add_argument("filename", type = str, help = "Filename of the dmg (e.g. 'UltiMaker-Cura-5.1.0-beta-Linux-X64.dmg')")
    args = parser.parse_args()
    build_dmg(args.source_path, args.dist_path, args.filename)
    sign(args.dist_path, args.filename)

    notarize_dmg = bool(os.environ.get("NOTARIZE_DMG", "TRUE"))
    if notarize_dmg:
        notarize(args.dist_path, args.filename)
