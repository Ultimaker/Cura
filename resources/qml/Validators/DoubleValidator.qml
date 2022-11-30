// Copyright (c) 2022 UltiMaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.
import QtQuick 2.15

RegularExpressionValidator
{
    property int maxBeforeDecimal: 10
    property int maxAfterDecimal: 10

    regularExpression:
    {
        // The build in DoubleValidator doesn't handle "," and "." interchangably.
        return "^-?[0-9]{0," + maxBeforeDecimal + "}[.,]?[0-9]{0," + maxAfterDecimal + "}$"
    }
}