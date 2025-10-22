#! /usr/bin/python

import git
import argparse
from difflib import Differ

def make_diff(previous_version: str, new_version: str, repo_path: str):
    repo = git.Repo(repo_path)
    commit_previous = repo.commit(previous_version)
    commit_new = repo.commit(new_version)
    return commit_previous.diff(commit_new)

def print_repo(repo: str):
    print("##############################################")
    print("##############################################")
    print(f"### Changes for {repo}")
    print("##############################################")
    print("##############################################")

def print_diff(diff):
    for diff_item in diff:
        path = diff_item.a_path if diff_item.a_path is not None else diff_item.b_path

        if ((not path.endswith(".py") and not path.endswith(".qml")) or
                "plugins/" in path or
                "packaging/" in path or
                "printer-linter/" in path or
                "tests/" in path or
                path.endswith("conanfile.py")):
            continue

        a_lines = diff_item.a_blob.data_stream.read().decode(
            'utf-8').splitlines() if diff_item.a_blob is not None else None
        b_lines = diff_item.b_blob.data_stream.read().decode(
            'utf-8').splitlines() if diff_item.b_blob is not None else None

        if a_lines is not None and b_lines is not None:
            changed_functions = {}
            relevant_diff_lines = []
            for diff_line in Differ().compare(a_lines, b_lines):
                if diff_line.startswith("- ") or diff_line.startswith("+ "):
                    relevant_diff_lines.append(diff_line)

            if relevant_diff_lines:
                print(f"================= Diff for file: {path}")
                print("\n".join(relevant_diff_lines))
        else:
            added = a_lines is None
            if a_lines is None:
                print(f"+++++++++++++++++ File {path} added")
            else:
                print(f"----------------- File {path} removed")

args_parser = argparse.ArgumentParser(description="Extract the changes between two release branches and create the proper SDK changelog")
args_parser.add_argument("previous_version", help="Git branch of the previous release, e.g. 5.10")
args_parser.add_argument("new_version", help="Git branch of the release in progress, e.g. 5.11")

args = args_parser.parse_args()

print_repo("Cura")
print_diff(make_diff(args.previous_version, args.new_version, "."))

print_repo("Uranium")
print_diff(make_diff(args.previous_version, args.new_version, "../Uranium")) ## Assumes repositories are besides each other
