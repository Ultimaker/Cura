import argparse

from typing import List

"""
    Takes in one of the po files in resources/i18n/[LANG_CODE]/cura.po and updates it with translations from a 
    new po file without changing the translation ordering. 
    This script should be used when we get a po file that has updated translations but is no longer correctly ordered 
    so the merge becomes messy.
    
    If you are importing files from lionbridge/smartling use lionbridge_import.py.
    
    Note: This does NOT include new strings, it only UPDATES existing strings   
"""


class Msg:
    def __init__(self, msgctxt: str = "", msgid: str = "", msgstr: str = "") -> None:
        self.msgctxt = msgctxt
        self.msgid = msgid
        self.msgstr = msgstr

    def __str__(self):
        return self.msgctxt + self.msgid + self.msgstr


def parsePOFile(filename: str) -> List[Msg]:
    messages = []
    with open(filename) as f:
        iterator = iter(f.readlines())
        for line in iterator:
            if line.startswith("msgctxt"):
                #  Start of a translation item block
                msg = Msg()
                msg.msgctxt = line

                while True:
                    line = next(iterator)
                    if line.startswith("msgid"):
                        msg.msgid = line
                        break

                while True:
                    #  msgstr can be split over multiple lines
                    line = next(iterator)
                    if line == "\n":
                        break
                    if line.startswith("msgstr"):
                        msg.msgstr = line
                    else:
                        msg.msgstr += line

                messages.append(msg)

        return messages


def getDifferentMessages(messages_original: List[Msg], messages_new: List[Msg]) -> List[Msg]:
    #  Return messages that have changed in messages_new
    different_messages = []

    for m_new in messages_new:
        for m_original in messages_original:
            if m_new.msgstr != m_original.msgstr \
                    and m_new.msgid == m_original.msgid and m_new.msgctxt == m_original.msgctxt \
                    and m_new.msgid != 'msgid ""\n':
                different_messages.append(m_new)

    return different_messages


def updatePOFile(input_filename: str, output_filename: str, messages: List[Msg]) -> None:
    # Takes a list of changed messages and writes a copy of input file with updated message strings
    with open(input_filename, "r") as input_file, open(output_filename, "w") as output_file:
        iterator = iter(input_file.readlines())
        for line in iterator:
            output_file.write(line)
            if line.startswith("msgctxt"):
                #  Start of translation block
                msgctxt = line

                msgid = next(iterator)
                output_file.write(msgid)

                #  Check for updated version of msgstr
                message = list(filter(lambda m: m.msgctxt == msgctxt and m.msgid == msgid, messages))
                if message and message[0]:
                    #  Write update translation
                    output_file.write(message[0].msgstr)

                    # Skip lines until next translation. This should skip multiline msgstr
                    while True:
                        line = next(iterator)
                        if line == "\n":
                            output_file.write(line)
                            break


if __name__ == "__main__":
    print("********************************************************************************************************************")
    print("This creates a new file 'updated.po' that is a copy of original_file with any changed translations from updated_file")
    print("This does not change the order of translations")
    print("This does not include new translations, only existing changed translations")
    print("Do not use this to import lionbridge/smarting translations")
    print("********************************************************************************************************************")
    parser = argparse.ArgumentParser(description="Update po file with translations from new po file. This ")
    parser.add_argument("original_file", type=str, help="Input .po file inside resources/i18n/[LANG]/")
    parser.add_argument("updated_file", type=str, help="Input .po file with updated translations added")
    args = parser.parse_args()

    messages_updated = parsePOFile(args.updated_file)
    messages_original = parsePOFile(args.original_file)
    different_messages = getDifferentMessages(messages_original, messages_updated)
    updatePOFile(args.original_file, "updated.po", different_messages)
