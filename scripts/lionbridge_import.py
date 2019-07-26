# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import argparse #To get the source directory from command line arguments.
import os #To find files from the source.
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
    print("Importing to Cura:", destination_cura())
    print("Importing to Uranium:", destination_uranium())

##  Gets the destination path to copy the translations for Cura to.
def destination_cura() -> str:
    return os.path.abspath(os.path.join(__file__, "..", "..", "resources", "i18n"))

##  Gets the destination path to copy the translations for Uranium to.
def destination_uranium() -> str:
    try:
        import UM
    except ImportError:
        relative_path = os.path.join(__file__, "..", "..", "..", "Uranium", "resources", "i18n", "uranium.pot")
        print(os.path.abspath(relative_path))
        if os.path.exists(relative_path):
            return os.path.abspath(relative_path)
        else:
            raise Exception("Can't find Uranium. Please put UM on the PYTHONPATH or put the Uranium folder next to the Cura folder.")
    return os.path.abspath(os.path.join(UM.__file__, "..", "..", "resources", "i18n"))

if __name__ == "__main__":
    argparser = argparse.ArgumentParser(description = "Import translation files from Lionbridge.")
    argparser.add_argument("source")
    args = argparser.parse_args()
    lionbridge_import(args.source)