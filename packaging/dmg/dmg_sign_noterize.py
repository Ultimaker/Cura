import os
import subprocess

SOURCE_DIR = os.environ.get("SOURCE_DIR", ".")
DIST_DIR = os.environ.get("DIST_DIR", os.path.join(SOURCE_DIR, "dist"))
DMG_PATH = "Ultimaker-Cura.dmg"
APP_PATH = os.path.join(DIST_DIR, "Ultimaker-Cura.app")
ULTIMAKER_CURA_DOMAIN = os.environ.get("ULTIMAKER_CURA_DOMAIN", "nl.ultimaker.cura")


def build_dmg() -> None:
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
                 DMG_PATH,
                 APP_PATH]

    subprocess.run(arguments)


def sign(file_path: str) -> None:
    codesign_executable = os.environ.get("CODESIGN", "codesign")
    codesign_identity = os.environ.get("CODESIGN_IDENTITY")

    arguments = [codesign_executable,
                 "-s", codesign_identity,
                 "--timestamp",
                 "-i", f"{ULTIMAKER_CURA_DOMAIN}.dmg",
                 file_path]

    subprocess.run(arguments)


def notarize() -> None:
    notarize_user = os.environ.get("MAC_NOTARIZE_USER")
    notarize_password = os.environ.get("MAC_NOTARIZE_PASSWORD")
    altool_executable = os.environ.get("ALTOOL_EXECUTABLE", "altool")

    arguments = [
        "xcrun", altool_executable,
        "--notarize-app",
        "--primary-bundle-id", ULTIMAKER_CURA_DOMAIN,
        "--username", notarize_user,
        "--password", notarize_password,
        "--file", DMG_PATH
    ]

    subprocess.run(arguments)


if __name__ == "__main__":
    build_dmg()
    sign(DMG_PATH)

    notarize_dmg = bool(os.environ.get("NOTARIZE_DMG", "TRUE"))
    if notarize_dmg:
        notarize()
