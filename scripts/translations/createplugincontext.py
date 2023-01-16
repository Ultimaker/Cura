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
import os.path
import collections
import json

debugoutput = False #set True to print debug output in scripty's logs

basedir = sys.argv[-1]
pottxt = ""


def appendMessage(file, field, value):
    global pottxt
    pottxt += "#: {0}\nmsgctxt \"{1}\"\nmsgid \"{2}\"\nmsgstr \"\"\n\n".format(file, field, value.replace("\n", "\\n").replace("\"", "\\\""))


if len(sys.argv) < 3:
    print("wrong number of args: %s" % sys.argv)
    print("\nUsage: python %s jsonfilenamelist basedir" % os.path.basename(sys.argv[0]))
else:
    json_filename = sys.argv[1]
    basedir = sys.argv[2]
    output_filename = sys.argv[3]

    with open(json_filename, "r", encoding = "utf-8") as data_file:
        error = False

        jsondatadict = json.load(data_file, object_pairs_hook=collections.OrderedDict)
        if "name" not in jsondatadict or ("api" not in jsondatadict and "supported_sdk_versions" not in jsondatadict) or "version" not in jsondatadict:
            print("The plugin.json file found on %s is invalid, ignoring it" % json_filename)
            exit(1)

        file = json_filename.replace(basedir, "")

        if "description" in jsondatadict:
            appendMessage(file, "description", jsondatadict["description"])
        if "name" in jsondatadict:
            appendMessage(file, "name", jsondatadict["name"])

    if pottxt != "":
        with open(output_filename, "a", encoding = "utf-8") as output_file:
            output_file.write(pottxt)
