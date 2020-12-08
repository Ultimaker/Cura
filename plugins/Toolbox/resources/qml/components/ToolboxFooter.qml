// Copyright (c) 2018 Ultimaker B.V.
// Toolbox is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3

import UM 1.1 as UM
import Cura 1.0 as Cura

Item
{
    id: footer
    width: parent.width
    anchors.bottom: parent.bottom
    height: visible ? UM.Theme.getSize("toolbox_footer").height : 0

    Label
    {
        text: catalog.i18nc("@info", "You will need to restart Cura before changes in packages have effect.")
        color: UM.Theme.getColor("text")
        height: UM.Theme.getSize("toolbox_footer_button").height
        verticalAlignment: Text.AlignVCenter
        wrapMode: Text.WordWrap
        anchors
        {
            top: restartButton.top
            left: parent.left
            leftMargin: UM.Theme.getSize("wide_margin").width
            right: restartButton.left
            rightMargin: UM.Theme.getSize("default_margin").width
        }
        renderType: Text.NativeRendering
    }

    Cura.PrimaryButton
    {
        id: restartButton
        anchors
        {
            top: parent.top
            topMargin: UM.Theme.getSize("default_margin").height
            right: parent.right
            rightMargin: UM.Theme.getSize("wide_margin").width
        }
        height: UM.Theme.getSize("toolbox_footer_button").height
        text: catalog.i18nc("@info:button, %1 is the application name", "Quit %1").arg(CuraApplication.applicationDisplayName)
        onClicked: toolbox.restart()
    }

    ToolboxShadow
    {
        visible: footer.visible
        anchors.bottom: footer.top
        reversed: true
    }
}
