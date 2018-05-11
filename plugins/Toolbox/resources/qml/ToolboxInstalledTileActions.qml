// Copyright (c) 2018 Ultimaker B.V.
// Toolbox is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import UM 1.1 as UM

Column
{
    width: UM.Theme.getSize("toolbox_action_button").width
    spacing: UM.Theme.getSize("narrow_margin").height

    Item
    {
        width: parent.width
        height: childrenRect.height
        visible: canUpdate
        Button
        {
            id: updateButton
            text: catalog.i18nc("@action:button", "Update")
            style: ButtonStyle
            {
                background: Rectangle
                {
                    implicitWidth: UM.Theme.getSize("toolbox_action_button").width
                    implicitHeight: UM.Theme.getSize("toolbox_action_button").height
                    color: control.hovered ? UM.Theme.getColor("primary_hover") : UM.Theme.getColor("primary")
                }
                label: Label
                {
                    text: control.text
                    color: control.hovered ? UM.Theme.getColor("button_text") : UM.Theme.getColor("button_text_hover")
                    verticalAlignment: Text.AlignVCenter
                    horizontalAlignment: Text.AlignHCenter
                    font: UM.Theme.getFont("default_bold")
                }
            }
            onClicked: toolbox.update(model.id)
        }
        ProgressBar
        {
            id: progressbar
            width: parent.width
            value: toolbox.isDownloading ? toolbox.downloadProgress : 0
            visible: toolbox.isDownloading
            style: ProgressBarStyle
            {
                background: Rectangle
                {
                    color: "transparent"
                    implicitHeight: UM.Theme.getSize("toolbox_action_button").height
                }
                progress: Rectangle
                {
                    // TODO Define a good color that fits the purpuse
                    color: "blue"
                    opacity: 0.5
                }
            }
        }
    }
    Button
    {
        id: removeButton
        text: catalog.i18nc("@action:button", "Uninstall")
        visible: !model.is_bundled
        enabled: !toolbox.isDownloading
        style: ButtonStyle
        {
            background: Rectangle
            {
                implicitWidth: UM.Theme.getSize("toolbox_action_button").width
                implicitHeight: UM.Theme.getSize("toolbox_action_button").height
                color: "transparent"
                border
                {
                    width: UM.Theme.getSize("default_lining").width
                    color: UM.Theme.getColor("lining")
                }
            }
            label: Label
            {
                text: control.text
                color: UM.Theme.getColor("text")
                verticalAlignment: Text.AlignVCenter
                horizontalAlignment: Text.AlignHCenter
            }
        }
        onClicked: toolbox.uninstall(model.id)
    }
}