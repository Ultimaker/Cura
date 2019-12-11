# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import argparse #To get the source directory from command line arguments.
import io # To fix encoding issues in Windows
import os #To find files from the source.
import os.path #To find files from the source and the destination path.

cura_files = {"cura", "fdmprinter.def.json", "fdmextruder.def.json"}
uranium_files = {"uranium"}

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

    for language in (directory for directory in os.listdir(source) if os.path.isdir(os.path.join(source, directory))):
        print("================ Processing language:", language, "================")
        directory = os.path.join(source, language)
        for file_pot in (file for file in os.listdir(directory) if file.endswith(".pot")):
            source_file = file_pot[:-4] #Strip extension.
            if source_file in cura_files:
                destination_file = os.path.join(destination_cura(), language.replace("-", "_"), source_file + ".po")
                print("Merging", source_file, "(Cura) into", destination_file)
            elif source_file in uranium_files:
                destination_file = os.path.join(destination_uranium(), language.replace("-", "_"), source_file + ".po")
                print("Merging", source_file, "(Uranium) into", destination_file)
            else:
                raise Exception("Unknown file: " + source_file + "... Is this Cura or Uranium?")

            with io.open(os.path.join(directory, file_pot), encoding = "utf8") as f:
                source_str = f.read()
            with io.open(destination_file, encoding = "utf8") as f:
                destination_str = f.read()
            result = merge(source_str, destination_str)
            with io.open(destination_file, "w", encoding = "utf8") as f:
                f.write(result)

##  Gets the destination path to copy the translations for Cura to.
#   \return Destination path for Cura.
def destination_cura() -> str:
    return os.path.abspath(os.path.join(__file__, "..", "..", "resources", "i18n"))

##  Gets the destination path to copy the translations for Uranium to.
#   \return Destination path for Uranium.
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

##  Merges translations from the source file into the destination file if they
#   were missing in the destination file.
#   \param source The contents of the source .po file.
#   \param destination The contents of the destination .po file.
def merge(source: str, destination: str) -> str:
    result_lines = []
    last_destination = {
        "msgctxt": "\"\"\n",
        "msgid": "\"\"\n",
        "msgstr": "\"\"\n",
        "msgid_plural": "\"\"\n"
    }

    current_state = "none"
    for line in destination.split("\n"):
        if line.startswith("msgctxt \""):
            current_state = "msgctxt"
            line = line[8:]
            last_destination[current_state] = ""
        elif line.startswith("msgid \""):
            current_state = "msgid"
            line = line[6:]
            last_destination[current_state] = ""
        elif line.startswith("msgstr \""):
            current_state = "msgstr"
            line = line[7:]
            last_destination[current_state] = ""
        elif line.startswith("msgid_plural \""):
            current_state = "msgid_plural"
            line = line[13:]
            last_destination[current_state] = ""

        if line.startswith("\"") and line.endswith("\""):
            last_destination[current_state] += line + "\n"
        else: #White lines or comment lines trigger us to search for the translation in the source file.
            if last_destination["msgstr"] == "\"\"\n" and last_destination["msgid"] != "\"\"\n": #No translation for this yet!
                last_destination["msgstr"] = find_translation(source, last_destination["msgctxt"], last_destination["msgid"]) #Actually place the translation in.
            if last_destination["msgctxt"] != "\"\"\n" or last_destination["msgid"] != "\"\"\n" or last_destination["msgid_plural"] != "\"\"\n" or last_destination["msgstr"] != "\"\"\n":
                if last_destination["msgctxt"] != "\"\"\n":
                    result_lines.append("msgctxt {msgctxt}".format(msgctxt = last_destination["msgctxt"][:-1])) #The [:-1] to strip the last newline.
                result_lines.append("msgid {msgid}".format(msgid = last_destination["msgid"][:-1]))
                if last_destination["msgid_plural"] != "\"\"\n":
                    result_lines.append("msgid_plural {msgid_plural}".format(msgid_plural = last_destination["msgid_plural"][:-1]))
                else:
                    result_lines.append("msgstr {msgstr}".format(msgstr = last_destination["msgstr"][:-1]))
            last_destination = {
                "msgctxt": "\"\"\n",
                "msgid": "\"\"\n",
                "msgstr": "\"\"\n",
                "msgid_plural": "\"\"\n"
            }

            result_lines.append(line) #This line itself.
    return "\n".join(result_lines)

##  Finds a translation in the source file.
#   \param source The contents of the source .po file.
#   \param msgctxt The ctxt of the translation to find.
#   \param msgid The id of the translation to find.
def find_translation(source: str, msgctxt: str, msgid: str) -> str:
    last_source = {
        "msgctxt": "\"\"\n",
        "msgid": "\"\"\n",
        "msgstr": "\"\"\n",
        "msgid_plural": "\"\"\n"
    }

    current_state = "none"
    for line in source.split("\n"):
        if line.startswith("msgctxt \""):
            current_state = "msgctxt"
            line = line[8:]
            last_source[current_state] = ""
        elif line.startswith("msgid \""):
            current_state = "msgid"
            line = line[6:]
            last_source[current_state] = ""
        elif line.startswith("msgstr \""):
            current_state = "msgstr"
            line = line[7:]
            last_source[current_state] = ""
        elif line.startswith("msgid_plural \""):
            current_state = "msgid_plural"
            line = line[13:]
            last_source[current_state] = ""

        if line.startswith("\"") and line.endswith("\""):
            last_source[current_state] += line + "\n"
        else: #White lines trigger us to process this translation. Is it the correct one?
            #Process the source and destination keys for comparison independent of newline technique.
            source_ctxt = "".join((line.strip()[1:-1] for line in last_source["msgctxt"].split("\n")))
            source_id = "".join((line.strip()[1:-1] for line in last_source["msgid"].split("\n")))
            dest_ctxt = "".join((line.strip()[1:-1] for line in msgctxt.split("\n")))
            dest_id = "".join((line.strip()[1:-1] for line in msgid.split("\n")))

            if source_ctxt == dest_ctxt and source_id == dest_id:
                if last_source["msgstr"] == "\"\"\n" and last_source["msgid_plural"] == "\"\"\n":
                    print("!!! Empty translation for {" + dest_ctxt + "}", dest_id, "!!!")
                return last_source["msgstr"]

            last_source = {
                "msgctxt": "\"\"\n",
                "msgid": "\"\"\n",
                "msgstr": "\"\"\n",
                "msgid_plural": "\"\"\n"
            }

    #Still here? Then the entire msgctxt+msgid combination was not found at all.
    print("!!! Missing translation for {" + msgctxt.strip() + "}", msgid.strip(), "!!!")
    return "\"\"\n"

if __name__ == "__main__":
    argparser = argparse.ArgumentParser(description = "Import translation files from Lionbridge.")
    argparser.add_argument("source")
    args = argparser.parse_args()
    lionbridge_import(args.source)