# Copyright (c) 2023 UltiMaker
# Cura is released under the terms of the LGPLv3 or higher.


import os
import argparse  # Command line arguments parsing and help.
import subprocess
from pathlib import Path

ULTIMAKER_CURA_DOMAIN = os.environ.get("ULTIMAKER_CURA_DOMAIN", "nl.ultimaker.cura")

def build_dmg(source_path: str, dist_path: str, filename: str, app_name: str) -> None:
    create_dmg_executable = os.environ.get("CREATE_DMG_EXECUTABLE", "create-dmg")

    arguments = [create_dmg_executable,
                 "--window-pos", "640", "360",
                 "--window-size", "690", "503",
                 "--app-drop-link", "520", "272",
                 "--volicon", f"{source_path}/packaging/icons/VolumeIcons_Cura.icns",
                 "--icon-size", "90",
                 "--icon", app_name, "169", "272",
                 "--eula", f"{source_path}/packaging/cura_license.txt",
                 "--background", f"{source_path}/packaging/MacOs/cura_background_dmg.png",
                 "--hdiutil-quiet",
                 f"{dist_path}/{filename}",
                 f"{dist_path}/{app_name}"]

    subprocess.run(arguments)


def build_pkg(dist_path: str, app_filename: str, component_filename: str, cura_version: str, installer_filename: str) -> None:
    """ Builds and signs the pkg installer.

    @param dist_path: Path to put output pkg in
    @param app_filename: name of the .app file to bundle inside the pkg
    @param component_filename: Name of the pkg component package to bundle the app in
    @param cura_version: The version is used when automatically replacing existing versions with the installer.
    @param installer_filename: Name of the installer that contains the component package
    """
    pkg_build_executable = os.environ.get("PKG_BUILD_EXECUTABLE", "pkgbuild")
    product_build_executable = os.environ.get("PRODUCT_BUILD_EXECUTABLE", "productbuild")
    codesign_identity = os.environ.get("CODESIGN_IDENTITY")

    # This builds the component package that contains UltiMaker-Cura.app. This component package will be bundled in a distribution package.
    pkg_build_arguments = [
        pkg_build_executable,
        "--identifier", f"{ULTIMAKER_CURA_DOMAIN}_{cura_version}", # If we want to replace previous version automatically remove {cure_version}
        "--component",
        Path(dist_path, app_filename),
        Path(dist_path, component_filename),
        "--install-location", "/Applications",
    ]

    if codesign_identity:
        pkg_build_arguments.extend(["--sign", codesign_identity])
    else:
        print("CODESIGN_IDENTITY missing. The installer is not being signed")

    subprocess.run(pkg_build_arguments)

    # This automatically generates a distribution.xml file that is used to build the installer.
    # If you want to make any changes to how the installer functions, this file should be changed to do that.
    # TODO: Use --product {property_list_file} to pull keys out of file for distribution.xml. This can be used to set min requirements
    distribution_creation_arguments = [
        product_build_executable,
        "--synthesize",
        "--package", Path(dist_path, component_filename),  # Package that will be inside installer
        Path(dist_path, "distribution.xml"),  # Output location for sythesized distributions file
    ]
    subprocess.run(distribution_creation_arguments)

    # This creates the distributable package (Installer)
    installer_creation_arguments = [
        product_build_executable,
        "--distribution", Path(dist_path, "distribution.xml"),
        "--package-path", dist_path,  # Where to find the component packages mentioned in distribution.xml (UltiMaker-Cura.pkg)
        Path(dist_path, installer_filename),
    ]

    if codesign_identity:
        installer_creation_arguments.extend(["--sign", codesign_identity])

    subprocess.run(installer_creation_arguments)


def notarize_file(dist_path: str, filename: str) -> None:
    """ Notarize a file. This takes 5+ minutes, there is indication that this step is successful."""
    notarize_user = os.environ.get("MAC_NOTARIZE_USER")
    notarize_password = os.environ.get("MAC_NOTARIZE_PASS")
    notarize_team = os.environ.get("MACOS_CERT_USER")
    notary_executable = os.environ.get("NOTARY_TOOL_EXECUTABLE", "notarytool")

    notarize_arguments = [
        "xcrun", notary_executable,
        "submit",
        "--apple-id", notarize_user,
        "--password", notarize_password,
        "--team-id", notarize_team,
        Path(dist_path, filename)
    ]

    subprocess.run(notarize_arguments)


def create_pkg_installer(filename: str,  dist_path: str, cura_version: str, app_name: str) -> None:
    """ Creates a pkg installer from {filename}.app called {filename}-Installer.pkg

    The final package structure is UltiMaker-Cura-XXX-Installer.pkg[UltiMaker-Cura.pkg[UltiMaker-Cura.app]]. The outer
    pkg file is a distributable pkg (Installer). Inside the distributable pkg there is a component pkg. The component
    pkg contains the .app file that will be installed in the users Applications folder.

    @param filename: The name of the app file and the app component package file without the extension
    @param dist_path: The location to read the app from and save the pkg to
    """

    filename_stem = Path(filename).stem
    cura_component_package_name = f"{filename_stem}-Component.pkg"  # This is a component package that is nested inside the installer, it contains the UltiMaker-Cura.app file This is the app file that will end up in your applications folder

    build_pkg(dist_path, app_name, cura_component_package_name, cura_version, filename)

    notarize = bool(os.environ.get("NOTARIZE_INSTALLER", "FALSE"))
    if notarize:
        notarize_file(dist_path, filename)


def create_dmg(filename: str, dist_path: str, source_path: str, app_name: str) -> None:
    """ Creates a dmg executable from UltiMaker-Cura.app named {filename}.dmg

    @param filename: The name of the app file and the output dmg file without the extension
    @param dist_path: The location to read the app from and save the dmg to
    @param source_path: The location of the project source files
    """

    build_dmg(source_path, dist_path, filename, app_name)

    notarize_dmg = bool(os.environ.get("NOTARIZE_DMG", "TRUE"))
    if notarize_dmg:
        notarize_file(dist_path, filename)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description = "Create installer for Cura.")
    parser.add_argument("--source_path", required = True, type = str, help = "Path to Pyinstaller source folder")
    parser.add_argument("--dist_path", required = True, type = str, help = "Path to Pyinstaller dist folder")
    parser.add_argument("--cura_conan_version", required = True, type = str, help = "The version of cura")
    parser.add_argument("--filename", required = True, type = str, help = "Filename of the pkg/dmg (e.g. 'UltiMaker-Cura-5.5.0-Macos-X64' or 'UltiMaker-Cura-5.5.0-beta.1-Macos-ARM64')")
    parser.add_argument("--build_pkg", action="store_true", default = False, help = "build the pkg")
    parser.add_argument("--build_dmg", action="store_true", default = True, help = "build the dmg")
    parser.add_argument("--app_name", required = True, type = str, help = "Filename of the .app that will be contained within the dmg/pkg")
    args = parser.parse_args()

    cura_version = args.cura_conan_version.split("/")[-1]

    app_name = f"{args.app_name}.app"

    if args.build_pkg:
        create_pkg_installer(f"{args.filename}.pkg", args.dist_path, cura_version, app_name)
    if args.build_dmg:
        create_dmg(f"{args.filename}.dmg", args.dist_path, args.source_path, app_name)
