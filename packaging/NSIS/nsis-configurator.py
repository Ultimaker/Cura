import shutil
import sys
from datetime import datetime

from pathlib import Path

from jinja2 import Template

if __name__ == "__main__":
    """
    - dist_loc: Location of distribution folder, as output by pyinstaller
    - nsi_jinja_loc: Jinja2 template to use
    - app_name: Should be "Ultimaker Cura".
    - main_app: Name of executable, e.g. Ultimaker-Cura.exe?
    - version_major: Major version number of Semver (e.g. 5).
    - version_minor: Minor version number of Semver (e.g. 0).
    - version_patch: Patch version number of Semver (e.g. 0).
    - version_build: A version number that gets manually incremented at each build.
    - company: Publisher of the application. Should be "Ultimaker B.V."
    - web_site: Website to find more information. Should be "https://ultimaker.com".
    - cura_license_file: Path to a license file in Cura. Should point to packaging/cura_license.txt in this repository.
    - compression_method: Compression algorithm to use to compress the data inside the executable. Should be ZLIB, ZBIP2 or LZMA.
    - cura_banner_img: Path to an image shown on the left in the installer. Should point to packaging/cura_banner_nsis.bmp in this repository.
    - icon_path: Path to the icon to use on the installer
    - destination: Where to put the installer after it's generated.
`    """
    for i, v in enumerate(sys.argv):
        print(f"{i} = {v}")
    dist_loc = Path(sys.argv[1])
    instdir = Path("$INSTDIR")
    dist_paths = [p.relative_to(dist_loc) for p in sorted(dist_loc.rglob("*")) if p.is_file()]
    mapped_out_paths = {}
    for dist_path in dist_paths:
        if "__pycache__" not in dist_path.parts:
            out_path = instdir.joinpath(dist_path).parent
            if out_path not in mapped_out_paths:
                mapped_out_paths[out_path] = [(dist_loc.joinpath(dist_path), instdir.joinpath(dist_path))]
            else:
                mapped_out_paths[out_path].append((dist_loc.joinpath(dist_path), instdir.joinpath(dist_path)))

    rmdir_paths = set()
    for rmdir_f in mapped_out_paths.values():
        for _, rmdir_p in rmdir_f:
            for rmdir in rmdir_p.parents:
                rmdir_paths.add(rmdir)

    rmdir_paths = sorted(list(rmdir_paths), reverse = True)[:-2]

    jinja_template_path = Path(sys.argv[2])
    with open(jinja_template_path, "r") as f:
        template = Template(f.read())

    nsis_content = template.render(
        app_name = sys.argv[3],
        main_app = sys.argv[4],
        version_major = sys.argv[5],
        version_minor = sys.argv[6],
        version_patch = sys.argv[7],
        version_build = sys.argv[8],
        company = sys.argv[9],
        web_site = sys.argv[10],
        year = datetime.now().year,
        cura_license_file = Path(sys.argv[11]),
        compression_method = sys.argv[12],  # ZLIB, BZIP2 or LZMA
        cura_banner_img = Path(sys.argv[13]),
        cura_icon = Path(sys.argv[14]),
        mapped_out_paths = mapped_out_paths,
        rmdir_paths = rmdir_paths,
        destination = Path(sys.argv[15])
    )

    with open(dist_loc.parent.joinpath(jinja_template_path.stem), "w") as f:
        f.write(nsis_content)

    shutil.copy(Path(__file__).absolute().parent.joinpath("fileassoc.nsh"), dist_loc.parent.joinpath("fileassoc.nsh"))
    icon_path = Path(sys.argv[14])
    shutil.copy(icon_path, dist_loc.joinpath(icon_path.name))

