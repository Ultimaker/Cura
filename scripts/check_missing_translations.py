#! /usr/bin/python3

import polib
import git
import sys
import os
import tempfile
from collections import OrderedDict


missing_keys = {}


def list_entries(file):
    entries = OrderedDict()

    for entry in file:
        if not entry.obsolete:
            msgctxt = entry.msgctxt
            if msgctxt is None:
                msgctxt = ''

            entries[(msgctxt, entry.msgid)] = entry

    return entries

def process_file(actual_file_path, previous_version_file_path, restore_missing):
    actual_file = polib.pofile(actual_file_path, wrapwidth=10000)
    previous_file = polib.pofile(previous_version_file_path, wrapwidth=10000)

    previous_entries = list_entries(previous_file)
    actual_entries = list_entries(actual_file)
    changed = False

    for key, entry in previous_entries.items():
        if key not in actual_entries:
            if key in missing_keys:
                missing_keys[key].append(actual_file_path)
            else:
                missing_keys[key] = [actual_file_path]

            if restore_missing:
                # Find the entry that was just before the one we need to re-insert
                previous_entry = None
                for entry_in_previous_file in previous_file:
                    if entry_in_previous_file == entry:
                        break
                    else:
                        previous_entry = entry_in_previous_file

                if previous_entry is None:
                    # The entry was at the very beginning
                    actual_file.insert(0, entry)
                else:
                    # Now find the position in the new file and re-insert the missing entry
                    index = 0
                    inserted = False
                    for entry_in_actual_file in actual_file:
                        if entry_in_actual_file.msgctxt == previous_entry.msgctxt and entry_in_actual_file.msgid == previous_entry.msgid:
                            actual_file.insert(index + 1, entry)
                            inserted = True
                            break
                        else:
                            index += 1

                    if not inserted:
                        actual_file.append(entry)

                changed = True

    if changed:
        print(f"Fixed file {actual_file_path}")
        actual_file.save()


try:
    previous_version = sys.argv[1]
    restore_missing = "--restore-missing" in sys.argv
except:
    print("Compares the translations present in the current folder with the same files from an other commit/branch. This will write a report.csv file containing the missing translations and the locations where they were expected. Make sure to run this script at the root of Cura/Uranium")
    print(f"How to use: {sys.argv[0]} previous_version [--restore-missing]")
    print("  --restore-missing    * Superbonus * This will also restore the translations missing from the previous file into the actual one")
    sys.exit(1)

repo = git.Repo('.')

languages_dir = os.path.join('resources', 'i18n')

language_dirs = [os.path.join(languages_dir, dir_path) for dir_path in os.listdir('resources/i18n')]
language_dirs = [language for language in language_dirs if os.path.isdir(language)]

for language_dir in language_dirs:
    for translation_file in os.listdir(language_dir):
        if translation_file.endswith('.po'):
            translation_file_path = os.path.join(language_dir, translation_file)
            blob = repo.commit(previous_version).tree / translation_file_path
            print(f'Processing file {translation_file_path}')
            with tempfile.NamedTemporaryFile(suffix='.po') as tmp_file:
                tmp_file.write(blob.data_stream.read())
                process_file(translation_file_path, tmp_file.name, restore_missing)

with open('report.csv', 'w') as report_file:
    for missing_key, files in missing_keys.items():
        report_file.write(';'.join(list(missing_key) + files))
        report_file.write('\n')
    print(f"Saved report to {report_file.name}")
