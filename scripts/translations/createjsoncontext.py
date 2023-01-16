#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Copyright 2014  Burkhard Lück <lueck@hube-lueck.de>

Permission to use, copy, modify, and distribute this software
and its documentation for any purpose and without fee is hereby
granted, provided that the above copyright notice appear in all
copies and that both that the copyright notice and this
permission notice and warranty disclaimer appear in supporting
documentation, and that the name of the author not be used in
advertising or publicity pertaining to distribution of the
software without specific, written prior permission.

The author disclaim all warranties with regard to this
software, including all implied warranties of merchantability
and fitness.  In no event shall the author be liable for any
special, indirect or consequential damages or any damages
whatsoever resulting from loss of use, data or profits, whether
in an action of contract, negligence or other tortious action,
arising out of or in connection with the use or performance of
this software.
"""

# This script generates a POT file from a JSON settings file. It
# has been adapted from createjsoncontext.py of KDE's translation
# scripts. It extracts the "label" and "description" values of
# the JSON file using the structure as used by Uranium settings files.

import sys
import os
import json
import time
import os.path
import collections

debugoutput = False #set True to print debug output in scripty's logs

basedir = sys.argv[-1]
pottxt = ""

def appendMessage(file, setting, field, value):
    global pottxt
    pottxt += "#: {0}\nmsgctxt \"{1} {2}\"\nmsgid \"{3}\"\nmsgstr \"\"\n\n".format(file, setting, field, value.replace("\n", "\\n").replace("\"", "\\\""))

def processSettings(file, settings):
    for name, value in settings.items():
        appendMessage(file, name, "label", value["label"])
        if "description" in value:
            appendMessage(file, name, "description", value["description"])

        if "warning_description" in value:
            appendMessage(file, name, "warning_description", value["warning_description"])

        if "error_description" in value:
            appendMessage(file, name, "error_description", value["error_description"])

        if "options" in value:
            for item, description in value["options"].items():
                appendMessage(file, name, "option {0}".format(item), description)

        if "children" in value:
            processSettings(file, value["children"])

def potheader():
    headertxt =  "#, fuzzy\n"
    headertxt += "msgid \"\"\n"
    headertxt += "msgstr \"\"\n"
    headertxt += "\"Project-Id-Version: Uranium json setting files\\n\"\n"
    headertxt += "\"Report-Msgid-Bugs-To: plugins@ultimaker.com\\n\"\n"
    headertxt += "\"POT-Creation-Date: %s+0000\\n\"\n" %time.strftime("%Y-%m-%d %H:%M")
    headertxt += "\"PO-Revision-Date: YEAR-MO-DA HO:MI+ZONE\\n\"\n"
    headertxt += "\"Last-Translator: FULL NAME <EMAIL@ADDRESS>\\n\"\n"
    headertxt += "\"Language-Team: LANGUAGE\\n\"\n"
    headertxt += "\"MIME-Version: 1.0\\n\"\n"
    headertxt += "\"Content-Type: text/plain; charset=UTF-8\\n\"\n"
    headertxt += "\"Content-Transfer-Encoding: 8bit\\n\"\n"
    headertxt += "\n"
    return headertxt

if len(sys.argv) < 3:
    print("wrong number of args: %s" % sys.argv)
    print("\nUsage: python %s jsonfilenamelist basedir" % os.path.basename(sys.argv[0]))
else:
    jsonfilename = sys.argv[1]
    basedir = sys.argv[2]
    outputfilename = sys.argv[3]

    with open(jsonfilename, "r", encoding = "utf-8") as data_file:
        error = False

        jsondatadict = json.load(data_file, object_pairs_hook=collections.OrderedDict)
        if "settings" not in jsondatadict:
            print(f"Nothing to translate in file: {jsondatadict}")
            exit(1)

        processSettings(jsonfilename.replace(basedir, ""), jsondatadict["settings"])

    if pottxt != "":
        with open(outputfilename, "w", encoding = "utf-8") as output_file:
            output_file.write(potheader())
            output_file.write(pottxt)
