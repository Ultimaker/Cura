// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.1

import UM 1.1 as UM
import Cura 1.0 as Cura

Button
{
    id: widget

    implicitHeight: UM.Theme.getSize("section_icon").height
    implicitWidth: UM.Theme.getSize("section_icon").width

    background: UM.RecolorImage
    {
        id: moreInformationIcon

        source: UM.Theme.getIcon("info")
        width: UM.Theme.getSize("section_icon").width
        height: UM.Theme.getSize("section_icon").height

        sourceSize.width: width
        sourceSize.height: height

        color: widget.hovered ? UM.Theme.getColor("primary") : UM.Theme.getColor("text_medium")
    }

    onClicked: popup.opened ? popup.close() : popup.open()

    Popup
    {
        id: popup

        y: -(height + UM.Theme.getSize("default_arrow").height + UM.Theme.getSize("thin_margin").height)
        x: parent.width - width + UM.Theme.getSize("thin_margin").width

        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutsideParent

        contentItem: PrintJobInformation
        {
            id: printJobInformation
            width: UM.Theme.getSize("action_panel_information_widget").width
        }

        background: UM.PointingRectangle
        {
            opacity: visible ? 1 : 0
            Behavior on opacity { NumberAnimation { duration: 100 } }
            color: UM.Theme.getColor("tool_panel_background")
            borderColor: UM.Theme.getColor("lining")
            borderWidth: UM.Theme.getSize("default_lining").width

            target: Qt.point(width - (widget.width / 2) - UM.Theme.getSize("thin_margin").width,
                            height + UM.Theme.getSize("default_arrow").height - UM.Theme.getSize("thin_margin").height)

            arrowSize: UM.Theme.getSize("default_arrow").width
        }
    }
}