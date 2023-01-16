#Creates the Pirate translation files.

import sys #To get command line arguments.
import pirateofdoom #Contains our translation dictionary.
import re #Case insensitive search and replace.
import random # Take random translation candidates

pot_file = sys.argv[1]
po_file = sys.argv[2]

#Translates English to Pirate.
def translate(english):
    english = english.replace("&", "") #Pirates don't take shortcuts.
    for eng, pir in pirateofdoom.pirate.items():
        matches = list(re.finditer(r"\b" + eng.lower() + r"\b", english.lower()))
        matches = [match.start(0) for match in matches]
        matches = reversed(sorted(matches))
        for position in matches:
            #Make sure the case is correct.
            uppercase = english[position].lower() != english[position]

            if isinstance(pir, list):
                pir = random.choice(pir)

            first_character = pir[0]
            rest_characters = pir[1:]
            if uppercase:
                first_character = first_character.upper()
            else:
                first_character = first_character.lower()
            pir = first_character + rest_characters

            english = english[:position] + pir + english[position + len(eng):]
    return english

translations = {}

last_id = ""
last_id_plural = ""
last_ctxt = ""
last_str = ""
state = "unknown"
with open(pot_file, encoding = "utf-8") as f:
    for line in f:
        if line.startswith("msgctxt"):
            state = "ctxt"
            if last_id != "":
                translations[(last_ctxt, last_id, last_id_plural)] = last_str
            last_ctxt = ""
            last_id = ""
            last_id_plural = ""
            last_str = ""
        elif line.startswith("msgid_plural"):
            state = "idplural"
        elif line.startswith("msgid"):
            state = "id"
        elif line.startswith("msgstr"):
            state = "str"

        if line.count('"') >= 2: #There's an ID on this line!
            line = line[line.find('"') + 1:] #Strip everything before the first ".
            line = line[:line.rfind('"')] #And after the last ".

            if state == "ctxt":
                last_ctxt += line #What's left is the context.
            elif state == "idplural":
                last_id_plural += line #Or the plural ID.
            elif state == "id":
                last_id += line #Or the ID.
            elif state == "str":
                last_str += line #Or the actual string.

for key, _ in translations.items():
    context, english, english_plural = key
    pirate = translate(english)
    pirate_plural = translate(english_plural)
    translations[key] = (pirate, pirate_plural)

with open(po_file, "w", encoding = "utf-8") as f:
    f.write("""msgid ""
msgstr ""
"Project-Id-Version: Pirate\\n"
"Report-Msgid-Bugs-To: plugins@ultimaker.com\\n"
"POT-Creation-Date: 1492\\n"
"PO-Revision-Date: 1492\\n"
"Last-Translator: Ghostkeeper and Awhiemstra\\n"
"Language-Team: Ghostkeeper and Awhiemstra\\n"
"Language: Pirate\\n"
"Lang-Code: en\\n"
"Country-Code: en_7S\\n"
"MIME-Version: 1.0\\n"
"Content-Type: text/plain; charset=UTF-8\\n"
"Content-Transfer-Encoding: 8bit\\n"
"Plural-Forms: nplurals=2; plural=(n != 1);\\n"
""")
    for key, value in translations.items():
        context, english, english_plural = key
        pirate, pirate_plural = value
        f.write('msgctxt "{context}"\n'.format(context = context))
        if english_plural == "": #No plurals in this item.
            f.write('msgid "{english}"\n'.format(english = english))
            f.write('msgstr "{pirate}"\n'.format(pirate = pirate))
        else:
            f.write('msgid "{english}"\n'.format(english = english))
            f.write('msgid_plural "{english_plural}"\n'.format(english_plural = english_plural))
            f.write('msgstr[0] "{pirate}"\n'.format(pirate = pirate))
            f.write('msgstr[1] "{pirate_plural}"\n'.format(pirate_plural = pirate_plural))
        f.write("\n") #Empty line.