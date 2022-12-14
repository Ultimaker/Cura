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
                 "--background", f"{source_path}/packaging/MacOs/cura_background_dmg.png",
                 f"{dist_path}/{filename}",
                 f"{dist_path}/UltiMaker-Cura.app"]

    subprocess.run(arguments)


def build_pkg(source_path: str, dist_path: str, app_filename: str, component_filename: str, installer_filename: str) -> None:
    pkg_build_executable = os.environ.get("PKG_BUILD_EXECUTABLE", "pkgbuild")
    product_build_executable = os.environ.get("PRODUCT_BUILD_EXECUTABLE", "productbuild")

    # This builds the component package that contains Ultimaker-Cura.app. This component package will be bundled in a distribution package.
    # TODO: sign the packgae with installer certificate
    pkg_build_arguments = [
        pkg_build_executable,
        "--component",
        f"{dist_path}/{app_filename}",
        f"{dist_path}/{component_filename}",
        "--install-location", "/Applications",
    ]
    print(f"pkg_build_arguments: {pkg_build_arguments}")
    subprocess.run(pkg_build_arguments)

    # This automatically generates a distribution.xml file that is used to build the installer.
    # If you want to make any changes to how the installer functions, this file should be changed to do that.
    # TODO: Use --product {property_list_file} to pull keys out of file for distribution.xml. This can be used to set min requirements
    # TODO: sign the packgae with installer certificate
    distribution_creation_arguments = [
        product_build_executable,
        "--synthesize",
        "--package", f"{dist_path}/{component_filename}",  # Package that will be inside installer
        f"{dist_path}/distribution.xml",  # Output location for sythesized distributions file
    ]
    print(f"distribution_creation_arguments: {distribution_creation_arguments}")
    subprocess.run(distribution_creation_arguments)

    # This creates the distributable package (Installer)
    installer_creation_arguments = [
        product_build_executable,
        "--distribution", f"{dist_path}/distribution.xml",
        "--package-path", dist_path,  # Where to find the component packages mentioned in distribution.xml (Ultimaker-Cura.pkg)
        f"{dist_path}/{installer_filename}",
    ]
    print(f"installer_creation_arguments: {installer_creation_arguments}")
    subprocess.run(installer_creation_arguments)


def code_sign(dist_path: str, filename: str) -> None:
    """ Sign a file using apple codesign. This uses a different certificate to package signing."""
    codesign_executable = os.environ.get("CODESIGN", "codesign")
    codesign_identity = os.environ.get("CODESIGN_IDENTITY")

    sign_arguments = [codesign_executable,
                 "-s", codesign_identity,
                 "--timestamp",
                 "-i", filename,  # This is by default derived from Info.plist or the filename. The documentation does not specify which, so it is explicit here. **This must be unique in the package**
                 f"{dist_path}/{filename}"]

    subprocess.run(sign_arguments)


def notarize_file(dist_path: str, filename: str) -> None:
    """ Notarize a file. This takes 5+ minutes, there is indication that this step is successful."""
    notarize_user = os.environ.get("MAC_NOTARIZE_USER")
    notarize_password = os.environ.get("MAC_NOTARIZE_PASS")
    altool_executable = os.environ.get("ALTOOL_EXECUTABLE", "altool")

    notarize_arguments = [
        "xcrun", altool_executable,
        "--notarize-app",
        "--primary-bundle-id", ULTIMAKER_CURA_DOMAIN,
        "--username", notarize_user,
        "--password", notarize_password,
        "--file", f"{dist_path}/{filename}"
    ]

    subprocess.run(notarize_arguments)


def create_pkg_installer(filename: str, dist_path: str, source_path: str) -> None:
    """ Creates a pkg installer from {filename}.app called {filename}-Installer.pkg

    The final package structure is Ultimaker-Cura-XXX-Installer.pkg[Ultimaker-Cura.pkg[Ultimaker-Cura.app]]

    @param filename: The name of the app file and the app component package file without the extension
    @param dist_path: The location to read the app from and save the pkg to
    @param source_path: The location of the project source files
    """
    installer_package_name = f"{filename}-Installer.pkg"
    cura_component_package_name = f"{filename}.pkg"  # This is a component package that is nested inside the installer, it contains the Ultimaker-Cura.app file
    app_name = "UltiMaker-Cura.app"  # This is the app file that will end up in your applications folder

    code_sign(dist_path, app_name)  # The app is signed using a different certificate than the package files
    build_pkg(source_path, dist_path, app_name, cura_component_package_name, installer_package_name)

    notarize = bool(os.environ.get("NOTARIZE_PKG", "TRUE"))
    if notarize:
        notarize_file(dist_path, installer_package_name)


def create_dmg(filename: str, dist_path: str, source_path: str) -> None:
    """ Creates a dmg executable from UltiMaker-Cura.app named {filename}.dmg

    @param filename: The name of the app file and the output dmg file without the extension
    @param dist_path: The location to read the app from and save the dmg to
    @param source_path: The location of the project source files
    """

    dmg_filename = f"{filename}.dmg"

    build_dmg(source_path, dist_path, dmg_filename)

    code_sign(dist_path, dmg_filename)

    notarize_dmg = bool(os.environ.get("NOTARIZE_DMG", "TRUE"))
    if notarize_dmg:
        notarize_file(dist_path, dmg_filename)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description = "Create dmg of Cura.")
    parser.add_argument("source_path", type=str, help="Path to Conan install Cura folder.")
    parser.add_argument("dist_path", type=str, help="Path to Pyinstaller dist folder")
    parser.add_argument("filename", type = str, help = "Filename of the dmg/pkg without the file extension (e.g. 'UltiMaker-Cura-5.1.0-beta-Linux-X64')")
    args = parser.parse_args()

    build_installer = bool(os.environ.get("BUILD_INSTALLER", "TRUE"))
    if build_installer:
        create_pkg_installer(args.filename, args.dist_path, args.source_path)

    build_dmg_executable = bool(os.environ.get("BUILD_DMG", "False"))
    if build_dmg_executable:
        create_dmg(args.filename, args.dist_path, args.source_path)
