# Copyright (c) 2022 UltiMaker
# Cura is released under the terms of the LGPLv3 or higher.


import argparse  # Command line arguments parsing and help.
import os
import shutil
import subprocess
import uuid
from datetime import datetime
from pathlib import Path

from jinja2 import Template


def work_path(filename: Path) -> Path:
    if not filename.is_absolute():
        return Path(os.getcwd(), filename.parent)
    else:
        return filename.parent


def generate_wxs(source_path: Path, dist_path: Path, filename: Path, app_name: str):
    source_loc = Path(os.getcwd(), source_path)
    dist_loc = Path(os.getcwd(), dist_path)
    work_loc = work_path(filename)
    work_loc.mkdir(parents=True, exist_ok=True)

    jinja_template_path = Path(source_loc.joinpath("packaging", "msi", "UltiMaker-Cura.wxs.jinja"))
    with open(jinja_template_path, "r") as f:
        template = Template(f.read())

    wxs_content = template.render(
        app_name=f"{app_name}",
        main_app="UltiMaker-Cura.exe",
        version=os.getenv('CURA_VERSION_FULL'),
        version_major=os.environ.get("CURA_VERSION_MAJOR"),
        version_minor=os.environ.get("CURA_VERSION_MINOR"),
        version_patch=os.environ.get("CURA_VERSION_PATCH"),
        company="UltiMaker",
        web_site="https://ultimaker.com",
        year=datetime.now().year,
        upgrade_code=str(uuid.uuid5(uuid.NAMESPACE_DNS, app_name)),
        cura_license_file=str(source_loc.joinpath("packaging", "msi", "cura_license.rtf")),
        cura_banner_top=str(source_loc.joinpath("packaging", "msi", "banner_top.bmp")),
        cura_banner_side=str(source_loc.joinpath("packaging", "msi", "banner_side.bmp")),
        cura_icon=str(source_loc.joinpath("packaging", "icons", "Cura.ico")),
    )

    with open(work_loc.joinpath("UltiMaker-Cura.wxs"), "w") as f:
        f.write(wxs_content)

    try:
        shutil.copy(source_loc.joinpath("packaging", "msi", "ExcludeComponents.xslt"),
                    work_loc.joinpath("ExcludeComponents.xslt"))
    except shutil.SameFileError:
        pass


def cleanup_artifacts(dist_path: Path):
    dist_loc = Path(os.getcwd(), dist_path)
    dirt = [d for d in dist_loc.rglob("__pycache__") if d.is_dir()]
    dirt += [d for d in dist_loc.rglob("*.dist-info") if d.is_dir()]
    for d in dirt:
        if d.exists():
            shutil.rmtree(d, ignore_errors=True)


def build(dist_path: Path, filename: Path):
    dist_loc = Path(os.getcwd(), dist_path)
    work_loc = work_path(filename)
    wxs_loc = work_loc.joinpath("UltiMaker-Cura.wxs")
    heat_loc = work_loc.joinpath("HeatFile.wxs")
    exclude_components_loc = work_loc.joinpath("ExcludeComponents.xslt")
    build_loc = work_loc.joinpath("build_msi")

    heat_command = ["heat",
                    "dir", f"{dist_loc.as_posix()}\\",
                    "-dr", "APPLICATIONFOLDER",
                    "-cg", "NewFilesGroup",
                    "-sw5150",  # Don't pollute logs with warnings from auto generated content
                    "-gg",
                    "-g1",
                    "-sf",
                    "-srd",
                    "-var", "var.CuraDir",
                    "-t", f"{exclude_components_loc.as_posix()}",
                    "-out", f"{heat_loc.as_posix()}"]
    subprocess.call(heat_command)

    build_command = ["candle",
                     "-arch", "x64",
                     f"-dCuraDir={dist_loc}\\",
                     "-ext", "WixFirewallExtension",
                     "-out", f"{build_loc.as_posix()}\\",
                     f"{wxs_loc.as_posix()}",
                     f"{heat_loc.as_posix()}"]
    subprocess.call(build_command)

    link_command = ["light",
                    f"{build_loc.joinpath(wxs_loc.name).with_suffix('.wixobj')}",
                    f"{build_loc.joinpath(heat_loc.name).with_suffix('.wixobj')}",
                    "-sw1076",  # Don't pollute logs with warnings from auto generated content
                    "-dcl:high",  # Use high compression ratio
                    "-sval",  # Disable ICE validation otherwise the CI complains
                    "-ext", "WixUIExtension",
                    "-ext", "WixFirewallExtension",
                    "-out", f"{work_loc.joinpath(filename.name)}"]
    subprocess.call(link_command)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create Windows msi installer of Cura.")
    parser.add_argument("source_path", type=Path, help="Path to Conan install Cura folder.")
    parser.add_argument("dist_path", type=Path, help="Path to Pyinstaller dist folder")
    parser.add_argument("filename", type=Path,
                        help="Filename of the exe (e.g. 'UltiMaker-Cura-5.1.0-beta-Windows-X64.msi')")
    parser.add_argument("name", type=str, help="App name (e.g. 'UltiMaker Cura')")
    args = parser.parse_args()
    generate_wxs(args.source_path.resolve(), args.dist_path.resolve(), args.filename.resolve(), args.name)
    cleanup_artifacts(args.dist_path.resolve())
    build(args.dist_path.resolve(), args.filename)
