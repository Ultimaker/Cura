// Copyright (c) 2016 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.
// Different than the name suggests, it is not always read-only.

import QtQuick 2.1
import QtQuick.Controls 2.1
import UM 1.5 as UM
import Cura 1.0 as Cura

Item
{
    id: base

    property alias text: textField.text

    signal editingFinished()

    property bool readOnly: false

    width: textField.width
    height: textField.height

    Cura.TextField
    {
        id: textField

        enabled: !base.readOnly

        anchors.fill: parent

        onEditingFinished: base.editingFinished()
        Keys.onEnterPressed: base.editingFinished()
        Keys.onReturnPressed: base.editingFinished()
    }
}
