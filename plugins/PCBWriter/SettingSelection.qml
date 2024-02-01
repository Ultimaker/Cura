// Copyright (c) 2024 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.3
import QtQuick.Window 2.2

import UM 1.5 as UM
import Cura 1.1 as Cura

RowLayout
{
    id: settingSelection

    UM.CheckBox
    {
        text: modelData.name
        Layout.preferredWidth: UM.Theme.getSize("setting").width
        checked: modelData.selected
        onClicked: modelData.selected = checked
    }

    UM.Label
    {
        text: modelData.value
    }
}
