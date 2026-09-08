# Copyright (c) 2025 UltiMaker
# Cura is released under the terms of the LGPLv3 or higher.


import os
import argparse  # Command line arguments parsing and help.
import subprocess
import semver

import shutil
from datetime import datetime

from pathlib import Path

from jinja2 import Template


def generate_nsi(source_path: str, dist_path: str, filename: str, version: str):
    dist_loc = Path(os.getcwd(), dist_path)
    source_loc = Path(os.getcwd(), source_path)
    instdir = Path("$INSTDIR")
    dist_paths = [p.relative_to(dist_loc.joinpath("UltiMaker-Cura")) for p in sorted(dist_loc.joinpath("UltiMaker-Cura").rglob("*")) if p.is_file()]
    parsed_version = semver.Version.parse(version)
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

    file_associations = [
        {"ext": "stl",   "prog_id": "Cura.model",        "type_description": "Standard Tessellation Language (STL) files",  "section_title": "*.STL files",         "feature_description": "Associate .STL (Standard Tessellation Language) files",         "optional": False,  "extra_exts": []},
        {"ext": "3mf",   "prog_id": "Cura.project",      "type_description": "3D Manufacturing Format (3MF) files",         "section_title": "*.3MF files",         "feature_description": "Associate .3MF (3D Manufacturing Format) project files",        "optional": False,  "extra_exts": []},
        {"ext": "obj",   "prog_id": "Cura.obj",          "type_description": "Wavefront OBJ files",                         "section_title": "*.OBJ files",         "feature_description": "Associate .OBJ (Wavefront Object) files",                       "optional": True,  "extra_exts": []},
        {"ext": "ply",   "prog_id": "Cura.ply",          "type_description": "Stanford Triangle Format (PLY) files",        "section_title": "*.PLY files",         "feature_description": "Associate .PLY (Stanford Triangle Format) files",               "optional": True,  "extra_exts": []},
        {"ext": "dae",   "prog_id": "Cura.dae",          "type_description": "COLLADA (DAE) files",                         "section_title": "*.DAE files",         "feature_description": "Associate .DAE (COLLADA) files",                                "optional": True,  "extra_exts": []},
        {"ext": "gltf",  "prog_id": "Cura.gltf",         "type_description": "glTF JSON files",                             "section_title": "*.GLTF files",        "feature_description": "Associate .GLTF (GL Transmission Format) files",                "optional": True,  "extra_exts": []},
        {"ext": "glb",   "prog_id": "Cura.glb",          "type_description": "glTF Binary files",                           "section_title": "*.GLB files",         "feature_description": "Associate .GLB (GL Transmission Format Binary) files",          "optional": True,  "extra_exts": []},
        {"ext": "amf",   "prog_id": "Cura.amf",          "type_description": "Additive Manufacturing Format (AMF) files",   "section_title": "*.AMF files",         "feature_description": "Associate .AMF (Additive Manufacturing Format) files",          "optional": True,  "extra_exts": []},
        {"ext": "x3d",   "prog_id": "Cura.x3d",          "type_description": "X3D files",                                   "section_title": "*.X3D files",         "feature_description": "Associate .X3D (Extensible 3D) files",                          "optional": True,  "extra_exts": []},
        {"ext": "ufp",   "prog_id": "Cura.ufp",          "type_description": "UltiMaker Format Package (UFP) files",        "section_title": "*.UFP files",         "feature_description": "Associate .UFP (UltiMaker Format Package) files",               "optional": False,  "extra_exts": []},
        {"ext": "gcode", "prog_id": "Cura.gcode",        "type_description": "G-code files",                                "section_title": "*.GCODE files",       "feature_description": "Associate .GCODE and .G (G-code) files",                        "optional": True,   "extra_exts": ["g"]},
    ]

    jinja_template_path = Path(source_loc.joinpath("packaging", "NSIS", "Ultimaker-Cura.nsi.jinja"))
    with open(jinja_template_path, "r") as f:
        template = Template(f.read())


    nsis_content = template.render(
        app_name = f"UltiMaker Cura {version}",
        main_app = "UltiMaker-Cura.exe",
        version = version,
        version_major = str(parsed_version.major),
        version_minor = str(parsed_version.minor),
        version_patch = str(parsed_version.patch),
        company = "UltiMaker",
        year = datetime.now().year,
        cura_license_file = str(source_loc.joinpath("packaging", "cura_license.txt")),
        compression_method = "LZMA",  # ZLIB, BZIP2 or LZMA
        cura_banner_img = str(source_loc.joinpath("packaging", "NSIS", "cura_banner_nsis.bmp")),
        cura_icon = str(source_loc.joinpath("packaging", "icons", "Cura.ico")),
        mapped_out_paths = mapped_out_paths,
        rmdir_paths = rmdir_paths,
        destination = filename,
        file_associations = file_associations,
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
    parser.add_argument("--source_path", type=str, help="Path to Conan install Cura folder.")
    parser.add_argument("--dist_path", type=str, help="Path to Pyinstaller dist folder")
    parser.add_argument("--filename", type=str, help="Filename of the exe (e.g. 'UltiMaker-Cura-5.1.0-beta-Windows-X64.exe')")
    parser.add_argument("--version", type=str, help="The full cura version, e.g. 5.9.0-beta.1+24132")
    args = parser.parse_args()
    generate_nsi(args.source_path, args.dist_path, args.filename, args.version)
    build(args.dist_path)
