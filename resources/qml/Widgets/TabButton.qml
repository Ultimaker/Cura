// Copyright (c) 2019 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3

import UM 1.3 as UM
import Cura 1.1 as Cura


//
// This is the default Cura Tab button which is a plaintext label.
//
UM.TabRowButton
{
    id: tabButton
    text: model.name

    contentItem: Label
    {
        anchors.centerIn: tabButton
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        text: tabButton.text
        font: tabButton.checked ? UM.Theme.getFont("medium_bold") : UM.Theme.getFont("medium")
        renderType: Text.NativeRendering
    }
}
