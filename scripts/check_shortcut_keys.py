#!/usr/bin/env python3
#
# This script checks for duplicate shortcut keys in all translation files.
#
import collections
import os
import sys
from typing import Optional

COLOR_WARNING = '\033[93m'
COLOR_ENDC = '\033[0m'

regex_patter = '(&[\w])' #"&[a-zA-Z0-9]" - Search char '&' and at least one character after it

# Directory where this python file resides
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))


class ShortcutKeysChecker:

    MSGCTXT = "msgctxt"  # Scope of the text . Like : msgctxt "@action:inmenu menubar:help"
    MSGID = "msgid"  # The id tag, also English text version
    MSGSTR = "msgstr"  # The translation tag

    def has_duplicates(self, filename: str) -> bool:
        """
        Checks if the given file has duplicate shortcut keys.
        """
        with open(filename, "r", encoding = "utf-8") as f:
            all_lines = f.readlines()

        all_lines = [l.strip() for l in all_lines]
        shortcut_dict = collections.defaultdict(dict)
        found_ctxt = False
        current_data = dict()
        current_field = None
        start_line = None

        for idx, line in enumerate(all_lines):
            if line.startswith(self.MSGCTXT):
                found_ctxt = True
                current_data.clear()
                current_field = self.MSGCTXT
                current_data[current_field] = self._fetch_data(line)
                start_line = idx
                continue

            elif found_ctxt and line.startswith(self.MSGID):
                current_field = self.MSGID
                current_data[current_field] = self._fetch_data(line)
                continue

            elif found_ctxt and line.startswith(self.MSGSTR):
                current_field = self.MSGSTR
                current_data[current_field] = self._fetch_data(line)
                continue

            elif found_ctxt and line.startswith('"'):
                data = line[1:-1]  # strip the beginning and ending double-quotes
                current_data[current_field] += data
                continue

            if current_data:
                self._process_translation(shortcut_dict, current_data, start_line)

            current_data.clear()
            current_field = None
            found_ctxt = False
            start_line = None

        return self._show_all_duplicates(shortcut_dict, filename)

    def _fetch_data(self, line: str) -> str:
        return (line.split(" ", 1)[-1])[1:-1]

    def _process_translation(self, shortcut_dict: dict, data_dict: dict, start_line: int) -> None:
        # Only check the ones with shortcuts
        msg = data_dict[self.MSGID]
        if data_dict[self.MSGSTR]:
            msg = data_dict[self.MSGSTR]
        shortcut_key = self._get_shortcut_key(msg)
        if shortcut_key is None:
            return

        msg_section = data_dict[self.MSGCTXT]
        keys_dict = shortcut_dict[msg_section]
        if shortcut_key not in keys_dict:
            keys_dict[shortcut_key] = {"shortcut_key": shortcut_key,
                                       "section": msg_section,
                                       "existing_lines": dict(),
                                       }
        existing_data_dict = keys_dict[shortcut_key]["existing_lines"]
        existing_data_dict[start_line] = {"message": msg,
                                          }

    def _get_shortcut_key(self, text: str) -> Optional[str]:
        key = None
        if text.count("&") == 1:
            idx = text.find("&") + 1
            if idx < len(text):
                character = text[idx]
                if not character.isspace():
                    key = character.lower()
        return key

    def _show_all_duplicates(self, shortcut_dict: dict, filename: str) -> bool:
        has_duplicates = False
        for keys_dict in shortcut_dict.values():
            for shortcut_key, data_dict in keys_dict.items():
                if len(data_dict["existing_lines"]) == 1:
                    continue

                has_duplicates = True

                print("")
                print("The following messages have the same shortcut key '%s':" % shortcut_key)
                print("  shortcut: '%s'" % data_dict["shortcut_key"])
                print("  section : '%s'" % data_dict["section"])
                for line, msg in data_dict["existing_lines"].items():
                    relative_filename = (filename.rsplit("..", 1)[-1])[1:]
                    print(" - [%s] L%7d : '%s'" % (relative_filename, line, msg["message"]))

        return has_duplicates


if __name__ == "__main__":
    checker = ShortcutKeysChecker()
    all_dirnames = [""]
    for _, dirnames, _ in os.walk(os.path.join(SCRIPT_DIR, "..", "resources", "i18n")):
        all_dirnames += [dn for dn in dirnames]
        break

    found_duplicates = False
    for dirname in all_dirnames:
        file_name = "cura.pot" if not dirname else "cura.po"
        file_path = os.path.join(SCRIPT_DIR, "..", "resources", "i18n", dirname, file_name)
        found_duplicates = found_duplicates or checker.has_duplicates(file_path)

    sys.exit(0 if not found_duplicates else 1)
