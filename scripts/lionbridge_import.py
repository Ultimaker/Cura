# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import argparse #To get the source directory from command line arguments.
import os.path #To find files from the source and the destination path.

##  Imports translation files from Lionbridge.
#
#   Lionbridge has a bit of a weird export feature. It exports it to the same
#   file type as what we imported, so that's a .pot file. However this .pot file
#   only contains the translations, so the header is completely empty. We need
#   to merge those translations into our existing files so that the header is
#   preserved.
def lionbridge_import(source: str) -> None:
    print("Importing from:", source)
    print("Importing to:", destination())

##  Gets the destination path to copy the translations to.
def destination() -> str:
    return os.path.abspath(os.path.join(__file__, "..", "..", "resources", "i18n"))

if __name__ == "__main__":
    argparser = argparse.ArgumentParser(description = "Import translation files from Lionbridge.")
    argparser.add_argument("source")
    args = argparser.parse_args()
    lionbridge_import(args.source)