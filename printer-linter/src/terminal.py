from argparse import ArgumentParser
from os import getcwd
from os import path
from pathlib import Path
from typing import List

import yaml

from printerlinter import factory
from printerlinter.diagnostic import Diagnostic
from printerlinter.formatters.def_json_formatter import DefJsonFormatter
from printerlinter.formatters.inst_cfg_formatter import InstCfgFormatter


def main() -> None:
    parser = ArgumentParser(
        description="UltiMaker Cura printer linting, static analysis and formatting of Cura printer definitions and other resources")
    parser.add_argument("--setting", required=False, type=Path, help="Path to the `.printer-linter` setting file")
    parser.add_argument("--report", required=False, type=Path, help="Path where the diagnostic report should be stored")
    parser.add_argument("--format", action="store_true", help="Format the files")
    parser.add_argument("--diagnose", action="store_true", help="Diagnose the files")
    parser.add_argument("--fix", action="store_true", help="Attempt to apply the suggested fixes on the files")
    parser.add_argument("Files", metavar="F", type=Path, nargs="+", help="Files or directories to format")

    args = parser.parse_args()
    files = extractFilePaths(args.Files)
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

    full_body_check = {"Diagnostics": []}

    for file in files:
        if not path.exists(file):
            print(f"Can't find the file: {file}")
            return

    if to_fix or to_diagnose:
        for file in files:
            diagnostics = diagnoseIssuesWithFile(file, settings)
            full_body_check["Diagnostics"].extend([d.toDict() for d in diagnostics])

            results = yaml.dump(full_body_check, default_flow_style=False, indent=4, width=240)

            if report:
                report.write_text(results)
            else:
                print(results)

    if to_fix:
        for file in files:
            if f"{file.as_posix()}" in full_body_check:
                applyFixesToFile(file, settings, full_body_check)

    if to_format:
        for file in files:
            applyFormattingToFile(file, settings)


def diagnoseIssuesWithFile(file: Path, settings: dict) -> List[Diagnostic]:
    """ For file, runs all diagnostic checks in settings and returns a list of diagnostics """
    linters = factory.getLinter(file, settings)

    if not linters:
        return []

    linter_results = []
    for linter in linters:
        linter_results.extend(list(filter(lambda d: d is not None, linter.check())))

    return linter_results


def applyFixesToFile(file, settings, full_body_check) -> None:
    if not file.exists():
        return
    ext = ".".join(file.name.split(".")[-2:])

    if ext == "def.json":
        issues = full_body_check[f"{file.as_posix()}"]
        for issue in issues:
            if issue["diagnostic"] == "diagnostic-definition-redundant-override" and settings["fixes"].get(
                    "diagnostic-definition-redundant-override", True):
                pass


def applyFormattingToFile(file: Path, settings) -> None:
    if not file.exists():
        return

    ext = ".".join(file.name.split(".")[-2:])

    if ext == "def.json":
        formatter = DefJsonFormatter(settings)
        formatter.formatFile(file)

    if ext == "inst.cfg":
        formatter = InstCfgFormatter(settings)
        formatter.formatFile(file)


def extractFilePaths(paths: List[Path]) -> List[Path]:
    """ Takes list of files and directories, returns the files as well as all files within directories as a List """
    file_paths = []
    for path in paths:
        if path.is_dir():
            file_paths.extend(path.rglob("**/*"))
        if not path.match("*"):
            file_paths.append(path)
        else:
            file_paths.extend(Path(*path.parts[:-1]).glob(path.parts[-1]))
            continue

    return file_paths


if __name__ == "__main__":
    main()
