import os
import subprocess

SOURCE_DIR = os.environ.get("SOURCE_DIR", ".")
DIST_DIR = os.environ.get("DIST_DIR", os.path.join(SOURCE_DIR, "dist"))

INSTALLER_FILENAME = "Ultimaker-Cura.dmg"
DMG_PATH = INSTALLER_FILENAME
ULTIMAKER_CURA_APP_PATH = os.path.join("dist/Ultimaker-Cura.app")

ULTIMAKER_CURA_DOMAIN = os.environ.get("ULTIMAKER_CURA_DOMAIN", "nl.ultimaker.cura")


def build_dmg() -> None:
    create_dmg_executable = os.environ.get("CREATE_DMG_EXECUTABLE", "create-dmg")

    arguments = [create_dmg_executable,
                    "--window-pos", "640",  "360",
                    "--window-size", "690",  "503",
                    "--app-drop-link", "520",  "272",
                    "--volicon", f"{SOURCE_DIR}/packaging/VolumeIcons_Cura.icns",
                    "--icon-size", "90",
                    "--icon", "Ultimaker-Cura.app", "169", "272",
                    "--eula", f"{SOURCE_DIR}/packaging/cura_license.txt",
                    "--background", f"{SOURCE_DIR}/packaging/cura_background_dmg.png",
                    DMG_PATH,
                    DIST_DIR]

    subprocess.run(arguments)


def sign() -> None:
    codesign_executable = os.environ.get("CODESIGN", "/usr/bin/codesign")
    codesign_identity = os.environ.get("CODESIGN_IDENTITY", "test")
    
    sign_command = f""" 
                    {codesign_executable}
                    -s {codesign_identity}
                    --timestamp 
                    -i {ULTIMAKER_CURA_DOMAIN}.dmg
                    {DMG_PATH}
                   """

    subprocess.Popen(sign_command)


def notarize() -> None:
    
    notarize_user = os.environ.get("NOTARIZE_USER")
    notarize_password = os.environ.get("NOTARIZE_PASSWORD")
    altool_executable = os.environ.get("ALTOOL_EXECUTABLE", "/Applications/Xcode.app/Contents/Developer/usr/bin/altool")
    
    notarize_command = f"""
                        xcrun {altool_executable}
                        --notarize-app
                        --primary-bundle-id {ULTIMAKER_CURA_DOMAIN}
                        --username {notarize_user}
                        --password {notarize_password}
                        --file {DMG_PATH}
                        """
    
    subprocess.Popen(notarize_command)


if __name__ == "__main__":
    build_dmg()
    sign()

    # notarize_dmg = bool(os.environ.get("NOTARIZE_DMG", "TRUE"))
    # if notarize_dmg:
    #     notarize()
    
