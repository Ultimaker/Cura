// Copyright (c) 2022 UltiMaker
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.15

RegularExpressionValidator
{
    regularExpression: new RegExp("^\[?(\s*-?[0-9]{0,11}\s*,)*(\s*-?[0-9]{0,11})\s*\]?$")
}