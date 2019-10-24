#!/usr/bin/env python3
#
# This script removes the given package entries in the bundled_packages JSON files. This is used by the PluginInstall
# CMake module.
#

import argparse
import collections
import json
import os
import sys


def find_json_files(work_dir: str) -> list:
    """
    Finds all JSON files in the given directory recursively and returns a list of those files in absolute paths.
    :param work_dir: The directory to look for JSON files recursively.
    :return: A list of JSON files in absolute paths that are found in the given directory.
    """
    json_file_list = []
    for root, dir_names, file_names in os.walk(work_dir):
        for file_name in file_names:
            abs_path = os.path.abspath(os.path.join(root, file_name))
            json_file_list.append(abs_path)
    return json_file_list


def remove_entries_from_json_file(file_path: str, entries: list) -> None:
    """
    Removes the given entries from the given JSON file. The file will modified in-place.
    :param file_path: The JSON file to modify.
    :param entries: A list of strings as entries to remove.
    :return: None
    """
    try:
        with open(file_path, "r", encoding = "utf-8") as f:
            package_dict = json.load(f, object_hook = collections.OrderedDict)
    except Exception as e:
        msg = "Failed to load '{file_path}' as a JSON file. This file will be ignored Exception: {e}"\
            .format(file_path = file_path, e = e)
        sys.stderr.write(msg + os.linesep)
        return

    for entry in entries:
        if entry in package_dict:
            del package_dict[entry]
            print("[INFO] Remove entry [{entry}] from [{file_path}]".format(file_path = file_path, entry = entry))

    try:
        with open(file_path, "w", encoding = "utf-8", newline = "\n") as f:
            json.dump(package_dict, f, indent = 4)
    except Exception as e:
        msg = "Failed to write '{file_path}' as a JSON file. Exception: {e}".format(file_path = file_path, e = e)
        raise IOError(msg)


def main() -> None:
    parser = argparse.ArgumentParser("mod_bundled_packages_json")
    parser.add_argument("-d", "--dir", dest = "work_dir",
                        help = "The directory to look for bundled packages JSON files, recursively.")
    parser.add_argument("entries", metavar = "ENTRIES", type = str, nargs = "+")

    args = parser.parse_args()

    json_file_list = find_json_files(args.work_dir)
    for json_file_path in json_file_list:
        remove_entries_from_json_file(json_file_path, args.entries)


if __name__ == "__main__":
    main()
