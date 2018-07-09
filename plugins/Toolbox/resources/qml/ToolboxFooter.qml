// Copyright (c) 2018 Ultimaker B.V.
// Toolbox is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import UM 1.1 as UM

Item
{
    id: footer
    width: parent.width
    anchors.bottom: parent.bottom
    height: visible ? Math.floor(UM.Theme.getSize("toolbox_footer").height) : 0
    Label
    {
        text: catalog.i18nc("@info", "You will need to restart Cura before changes in packages have effect.")
        color: UM.Theme.getColor("text")
        height: Math.floor(UM.Theme.getSize("toolbox_footer_button").height)
        verticalAlignment: Text.AlignVCenter
        anchors
        {
            top: restartButton.top
            left: parent.left
            leftMargin: UM.Theme.getSize("wide_margin").width
            right: restartButton.right
            rightMargin: UM.Theme.getSize("default_margin").width
        }
     
    }
    Button
    {
        id: restartButton
        text: catalog.i18nc("@info:button", "Quit Cura")
        anchors
        {
            top: parent.top
            topMargin: UM.Theme.getSize("default_margin").height
            right: parent.right
            rightMargin: UM.Theme.getSize("wide_margin").width
        }
        iconName: "dialog-restart"
        onClicked: toolbox.restart()
        style: ButtonStyle
        {
            background: Rectangle
            {
                implicitWidth: UM.Theme.getSize("toolbox_footer_button").width
                implicitHeight: Math.floor(UM.Theme.getSize("toolbox_footer_button").height)
                color: control.hovered ? UM.Theme.getColor("primary_hover") : UM.Theme.getColor("primary")
            }
            label: Label
            {
                color: UM.Theme.getColor("button_text")
                font: UM.Theme.getFont("default_bold")
                text: control.text
                verticalAlignment: Text.AlignVCenter
                horizontalAlignment: Text.AlignHCenter
            }
        }
    }
    ToolboxShadow
    {
        visible: footer.visible
        anchors.bottom: footer.top
        reversed: true
    }
}
