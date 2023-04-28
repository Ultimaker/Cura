// Copyright (c) 2022 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.3
import QtQuick.Window 2.2

import UM 1.5 as UM
import Cura 1.1 as Cura

Row
{
    property alias leftLabelText: leftLabel.text
    property alias rightLabelText: rightLabel.text

    width: parent.width
    height: visible ? childrenRect.height : 0

    UM.Label
    {
        id: leftLabel
        text: catalog.i18nc("@action:label", "Type")
        width: Math.round(parent.width / 4)
        wrapMode: Text.WordWrap
    }
    UM.Label
    {
        id: rightLabel
        text: manager.machineType
        width: Math.round(parent.width / 3)
        wrapMode: Text.WordWrap
    }
}