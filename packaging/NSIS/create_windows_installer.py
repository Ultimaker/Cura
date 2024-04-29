# Copyright (c) 2022 UltiMaker
# Cura is released under the terms of the LGPLv3 or higher.


import os
import argparse  # Command line arguments parsing and help.
import subprocess

import shutil
from datetime import datetime

from pathlib import Path

from jinja2 import Template


def generate_nsi(source_path: str, dist_path: str, filename: str):
    dist_loc = Path(os.getcwd(), dist_path)
    source_loc = Path(os.getcwd(), source_path)
    instdir = Path("$INSTDIR")
    dist_paths = [p.relative_to(dist_loc.joinpath("UltiMaker-Cura")) for p in sorted(dist_loc.joinpath("UltiMaker-Cura").rglob("*")) if p.is_file()]
    mapped_out_paths = {}
    for dist_path in dist_paths:
        if "__pycache__" not in dist_path.parts:
            out_path = instdir.joinpath(dist_path).parent
            if out_path not in mapped_out_paths:
                mapped_out_paths[out_path] = [(dist_loc.joinpath("UltiMaker-Cura", dist_path), instdir.joinpath(dist_path))]
            else:
                mapped_out_paths[out_path].append((dist_loc.joinpath("UltiMaker-Cura", dist_path), instdir.joinpath(dist_path)))

    rmdir_paths = set()
    for rmdir_f in mapped_out_paths.values():
        for _, rmdir_p in rmdir_f:
            for rmdir in rmdir_p.parents:
                rmdir_paths.add(rmdir)

    rmdir_paths = sorted(list(rmdir_paths), reverse = True)[:-2]  # Removes the `.` and `..` from the list

    jinja_template_path = Path(source_loc.joinpath("packaging", "NSIS", "Ultimaker-Cura.nsi.jinja"))
    with open(jinja_template_path, "r") as f:
        template = Template(f.read())


    nsis_content = template.render(
        app_name = f"UltiMaker Cura {os.getenv('CURA_VERSION_FULL')}",
        main_app = "UltiMaker-Cura.exe",
        version = os.getenv('CURA_VERSION_FULL'),
        version_major = os.environ.get("CURA_VERSION_MAJOR"),
        version_minor = os.environ.get("CURA_VERSION_MINOR"),
        version_patch = os.environ.get("CURA_VERSION_PATCH"),
        company = "UltiMaker",
        web_site = "https://ultimaker.com",
        year = datetime.now().year,
        cura_license_file = str(source_loc.joinpath("packaging", "cura_license.txt")),
        compression_method = "LZMA",  # ZLIB, BZIP2 or LZMA
        cura_banner_img = str(source_loc.joinpath("packaging", "NSIS", "cura_banner_nsis.bmp")),
        cura_icon = str(source_loc.joinpath("packaging", "icons", "Cura.ico")),
        mapped_out_paths = mapped_out_paths,
        rmdir_paths = rmdir_paths,
        destination = filename
    )

    with open(dist_loc.joinpath("UltiMaker-Cura.nsi"), "w") as f:
        f.write(nsis_content)

    shutil.copy(source_loc.joinpath("packaging", "NSIS", "fileassoc.nsh"), dist_loc.joinpath("fileassoc.nsh"))


def build(dist_path: str):
    dist_loc = Path(os.getcwd(), dist_path)
    command = ["makensis", "/V2", "/P4", str(dist_loc.joinpath("UltiMaker-Cura.nsi"))]
    subprocess.run(command)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description = "Create Windows exe installer of Cura.")
    parser.add_argument("source_path", type=str, help="Path to Conan install Cura folder.")
    parser.add_argument("dist_path", type=str, help="Path to Pyinstaller dist folder")
    parser.add_argument("filename", type = str, help = "Filename of the exe (e.g. 'UltiMaker-Cura-5.1.0-beta-Windows-X64.exe')")
    args = parser.parse_args()
    generate_nsi(args.source_path, args.dist_path, args.filename)
    build(args.dist_path)
