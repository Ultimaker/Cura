// Copyright (c) 2022 UltiMaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.
import QtQuick 2.15

RegularExpressionValidator
{
    property int maxNumbers: 12

    regularExpression: new RegExp("^-?[0-9]{0,%0}$".arg(maxNumbers))
}