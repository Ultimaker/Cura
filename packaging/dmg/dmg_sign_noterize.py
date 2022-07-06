import os
import argparse  # Command line arguments parsing and help.
import subprocess

SOURCE_DIR = os.environ.get("SOURCE_DIR", ".")
DIST_DIR = os.environ.get("DIST_DIR", os.path.join(SOURCE_DIR, "dist"))
APP_PATH = os.path.join(DIST_DIR, "Ultimaker-Cura.app")
ULTIMAKER_CURA_DOMAIN = os.environ.get("ULTIMAKER_CURA_DOMAIN", "nl.ultimaker.cura")


def build_dmg(filename: str) -> None:
    create_dmg_executable = os.environ.get("CREATE_DMG_EXECUTABLE", "create-dmg")

    arguments = [create_dmg_executable,
                 "--window-pos", "640", "360",
                 "--window-size", "690", "503",
                 "--app-drop-link", "520", "272",
                 "--volicon", f"{SOURCE_DIR}/packaging/icons/VolumeIcons_Cura.icns",
                 "--icon-size", "90",
                 "--icon", "Ultimaker-Cura.app", "169", "272",
                 "--eula", f"{SOURCE_DIR}/packaging/cura_license.txt",
                 "--background", f"{SOURCE_DIR}/packaging/icons/cura_background_dmg.png",
                 filename,
                 APP_PATH]

    subprocess.run(arguments)


def sign(filename: str) -> None:
    codesign_executable = os.environ.get("CODESIGN", "codesign")
    codesign_identity = os.environ.get("CODESIGN_IDENTITY")

    arguments = [codesign_executable,
                 "-s", codesign_identity,
                 "--timestamp",
                 "-i", f"{ULTIMAKER_CURA_DOMAIN}.dmg",  # TODO: check if this really should have the extra dmg. We seem to be doing this also in the old Rundeck scripts
                 filename]

    subprocess.run(arguments)


def notarize(filename: str) -> None:
    notarize_user = os.environ.get("MAC_NOTARIZE_USER")
    notarize_password = os.environ.get("MAC_NOTARIZE_PASSWORD")
    altool_executable = os.environ.get("ALTOOL_EXECUTABLE", "altool")

    arguments = [
        "xcrun", altool_executable,
        "--notarize-app",
        "--primary-bundle-id", ULTIMAKER_CURA_DOMAIN,
        "--username", notarize_user,
        "--password", notarize_password,
        "--file", filename
    ]

    subprocess.run(arguments)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description = "Create AppImages of Cura.")
    parser.add_argument("filename", type = str, help = "Filename of the dmg (e.g. 'Ultimaker-Cura-5.1.0-beta-Linux-X64.dmg')")
    args = parser.parse_args()
    build_dmg(args.filename)
    sign(args.filename)

    notarize_dmg = bool(os.environ.get("NOTARIZE_DMG", "TRUE"))
    if notarize_dmg:
        notarize(args.filename)
