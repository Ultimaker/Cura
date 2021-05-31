// Copyright (c) 2018 Ultimaker B.V.
// Toolbox is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import UM 1.1 as UM

Item
{
    id: sidebar
    height: parent.height
    width: UM.Theme.getSize("toolbox_back_column").width
    anchors
    {
        top: parent.top
        left: parent.left
        topMargin: UM.Theme.getSize("wide_margin").height
        leftMargin: UM.Theme.getSize("default_margin").width
        rightMargin: UM.Theme.getSize("default_margin").width
    }
    Button
    {
        id: button
        text: catalog.i18nc("@action:button", "Back")
        enabled: !toolbox.isDownloading
        UM.RecolorImage
        {
            id: backArrow
            anchors
            {
                verticalCenter: parent.verticalCenter
                left: parent.left
                rightMargin: UM.Theme.getSize("default_margin").width
            }
            width: UM.Theme.getSize("standard_arrow").width
            height: UM.Theme.getSize("standard_arrow").height
            sourceSize
            {
                width: width
                height: height
            }
            color: button.enabled ? (button.hovered ? UM.Theme.getColor("primary") : UM.Theme.getColor("text")) : UM.Theme.getColor("text_inactive")
            source: UM.Theme.getIcon("arrow_left")
        }
        width: UM.Theme.getSize("toolbox_back_button").width
        height: UM.Theme.getSize("toolbox_back_button").height
        onClicked:
        {
            toolbox.viewPage = "overview"
            if (toolbox.viewCategory == "material")
            {
                toolbox.filterModelByProp("authors", "package_types", "material")
            }
            else if (toolbox.viewCategory == "plugin")
            {
                toolbox.filterModelByProp("packages", "type", "plugin")
            }

        }
        style: ButtonStyle
        {
            background: Rectangle
            {
                color: "transparent"
            }
            label: Label
            {
                id: labelStyle
                text: control.text
                color: control.enabled ? (control.hovered ? UM.Theme.getColor("primary") : UM.Theme.getColor("text")) : UM.Theme.getColor("text_inactive")
                font: UM.Theme.getFont("medium_bold")
                horizontalAlignment: Text.AlignLeft
                anchors
                {
                    left: parent.left
                    leftMargin: UM.Theme.getSize("default_margin").width
                }
                width: control.width
                renderType: Text.NativeRendering
            }
        }
    }
}
