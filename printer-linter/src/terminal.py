import configparser
import json
import re
from argparse import ArgumentParser
from collections import OrderedDict
from os import getcwd
from pathlib import Path

import yaml

from printerlinter import factory


def examineFile(file, settings, full_body_check):
    patient = factory.create(file, settings)
    if patient is None:
        return

    for diagnostic in patient.check():
        if diagnostic:
            full_body_check["Diagnostics"].append(diagnostic.toDict())


def fixFile(file, settings, full_body_check):
    if not file.exists():
        return
    ext = ".".join(file.name.split(".")[-2:])

    if ext == "def.json":
        issues = full_body_check[f"{file.as_posix()}"]
        for issue in issues:
            if issue["diagnostic"] == "diagnostic-definition-redundant-override" and settings["fixes"].get(
                    "diagnostic-definition-redundant-override", True):
                pass


def formatFile(file: Path, settings):
    if not file.exists():
        return
    ext = ".".join(file.name.split(".")[-2:])

    if ext == "def.json":
        definition = json.loads(file.read_text())
        content = json.dumps(definition, indent=settings["format"].get("format-definition-indent", 4),
                             sort_keys=settings["format"].get("format-definition-sort-keys", True))

        if settings["format"].get("format-definition-bracket-newline", True):
            newline = re.compile(r"(\B\s+)(\"[\w\"]+)(\:\s\{)")
            content = newline.sub(r"\1\2:\1{", content)

        if settings["format"].get("format-definition-paired-coordinate-array", True):
            paired_coordinates = re.compile(r"(\[)\s+(-?\d*),\s*(-?\d*)\s*(\])")
            content = paired_coordinates.sub(r"\1 \2, \3 \4", content)

        file.write_text(content)

    if ext == "inst.cfg":
        config = configparser.ConfigParser()
        config.read(file)

        if settings["format"].get("format-profile-sort-keys", True):
            for section in config._sections:
                config._sections[section] = OrderedDict(sorted(config._sections[section].items(), key=lambda t: t[0]))
            config._sections = OrderedDict(sorted(config._sections.items(), key=lambda t: t[0]))

        with open(file, "w") as f:
            config.write(f, space_around_delimiters=settings["format"].get("format-profile-space-around-delimiters", True))


def main():
    parser = ArgumentParser(
        description="UltiMaker Cura printer linting, static analysis and formatting of Cura printer definitions and other resources")
    parser.add_argument("--setting", required=False, type=Path, help="Path to the `.printer-linter` setting file")
    parser.add_argument("--report", required=False, type=Path, help="Path where the diagnostic report should be stored")
    parser.add_argument("--format", action="store_true", help="Format the files")
    parser.add_argument("--diagnose", action="store_true", help="Diagnose the files")
    parser.add_argument("--fix", action="store_true", help="Attempt to apply the suggested fixes on the files")
    parser.add_argument("Files", metavar="F", type=Path, nargs="+", help="Files or directories to format")

    args = parser.parse_args()
    files = args.Files
    setting_path = args.setting
    to_format = args.format
    to_fix = args.fix
    to_diagnose = args.diagnose
    report = args.report

    if not setting_path:
        setting_path = Path(getcwd(), ".printer-linter")

    if not setting_path.exists():
        print(f"Can't find the settings: {setting_path}")
        return

    with open(setting_path, "r") as f:
        settings = yaml.load(f, yaml.FullLoader)

    if to_fix or to_diagnose:
        full_body_check = {"Diagnostics": []}
        for file in files:
            if file.is_dir():
                for fp in file.rglob("**/*"):
                    examineFile(fp, settings, full_body_check)
            else:
                examineFile(file, settings, full_body_check)

            results = yaml.dump(full_body_check, default_flow_style=False, indent=4, width=240)
            if report:
                report.write_text(results)
            else:
                print(results)

        if to_fix:
            for file in files:
                if file.is_dir():
                    for fp in file.rglob("**/*"):
                        if f"{file.as_posix()}" in full_body_check:
                            fixFile(fp, settings, full_body_check)
                else:
                    if f"{file.as_posix()}" in full_body_check:
                        fixFile(file, settings, full_body_check)

    if to_format:
        for file in files:
            if file.is_dir():
                for fp in file.rglob("**/*"):
                    formatFile(fp, settings)
            else:
                formatFile(file, settings)


if __name__ == "__main__":
    main()
