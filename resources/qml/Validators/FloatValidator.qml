// Copyright (c) 2022 UltiMaker
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.15

RegularExpressionValidator
{
    property int maxBeforeDecimal: 11
    property int maxAfterDecimal: 3

    regularExpression: new RegExp("^-?[0-9]{0,%0}[.,]?[0-9]{0,%1}$".arg(maxBeforeDecimal).arg(maxAfterDecimal))
}