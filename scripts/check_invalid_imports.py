import os
import re
import sys
from pathlib import Path

"""
Run this file with the Cura project root as the working directory
"""

class InvalidImportsChecker:
    # compile regex
    REGEX = re.compile(r"^\s*(from plugins|import plugins)")

    def check(self):
        """ Checks for invalid imports

        :return: True if checks passed, False when the test fails
        """
        cwd = os.getcwd()
        cura_result = checker.check_dir(os.path.join(cwd, "cura"))
        plugins_result = checker.check_dir(os.path.join(cwd, "plugins"))
        result = cura_result and plugins_result
        if not result:
            print("error: sources contain invalid imports. Use relative imports when referencing plugin source files")

        return result

    def check_dir(self, root_dir: str) -> bool:
        """ Checks a directory for invalid imports

        :return: True if checks passed, False when the test fails
        """
        passed = True
        for path_like in Path(root_dir).rglob('*.py'):
            if not self.check_file(str(path_like)):
                passed = False

        return passed

    def check_file(self, file_path):
        """ Checks a file for invalid imports

        :return: True if checks passed, False when the test fails
        """
        passed = True
        with open(file_path, 'r', encoding = "utf-8") as inputFile:
            # loop through each line in file
            for line_i, line in enumerate(inputFile, 1):
                # check if we have a regex match
                match = self.REGEX.search(line)
                if match:
                    path = os.path.relpath(file_path)
                    print("{path}:{line_i}:{match}".format(path=path, line_i=line_i, match=match.group(1)))
                    passed = False
        return passed


if __name__ == "__main__":
    checker = InvalidImportsChecker()
    sys.exit(0 if checker.check() else 1)
