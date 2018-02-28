// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.0

import UM 1.2 as UM
import Cura 1.0 as Cura

ComboBox
{
    id: control

    property var panelWidth: control.width

    model: ListModel {

        ListElement {
            name: "Configuration 1"
            color: "yellow"
        }
        ListElement {
            name: "Configuration 2"
            color: "black"
        }
        ListElement {
            name: "Configuration 3"
            color: "green"
        }
        ListElement {
            name: "Configuration 4"
            color: "red"
        }
    }

    textRole: "name"

    indicator: UM.RecolorImage
    {
        id: downArrow
        x: control.width - width - control.rightPadding
        y: control.topPadding + Math.round((control.availableHeight - height) / 2)

        source: UM.Theme.getIcon("arrow_bottom")
        width: UM.Theme.getSize("standard_arrow").width
        height: UM.Theme.getSize("standard_arrow").height
        sourceSize.width: width + 5 * screenScaleFactor
        sourceSize.height: width + 5 * screenScaleFactor

        color: UM.Theme.getColor("setting_control_text");
    }

    background: Rectangle
    {
        color:
        {
            if (!enabled)
            {
                return UM.Theme.getColor("setting_control_disabled");
            }
            if (control.hovered || control.activeFocus)
            {
                return UM.Theme.getColor("setting_control_highlight");
            }
            return UM.Theme.getColor("setting_control");
        }
        border.width: UM.Theme.getSize("default_lining").width
        border.color:
        {
            if (!enabled)
            {
                return UM.Theme.getColor("setting_control_disabled_border")
            }
            if (control.hovered || control.activeFocus)
            {
                return UM.Theme.getColor("setting_control_border_highlight")
            }
            return UM.Theme.getColor("setting_control_border")
        }
    }

    contentItem: Label
    {
        anchors.verticalCenter: parent.verticalCenter
        anchors.left: parent.left
        anchors.leftMargin: UM.Theme.getSize("setting_unit_margin").width
        anchors.right: downArrow.left
        rightPadding: swatch.width + UM.Theme.getSize("setting_unit_margin").width

        text: "HOLA"
        renderType: Text.NativeRendering
        font: UM.Theme.getFont("default")
        color: enabled ? UM.Theme.getColor("setting_control_text") : UM.Theme.getColor("setting_control_disabled_text")

        elide: Text.ElideRight
        verticalAlignment: Text.AlignVCenter
    }

    popup: Popup {
        y: control.height - UM.Theme.getSize("default_lining").height
        x: control.width - width
        width: panelWidth
        implicitHeight: contentItem.implicitHeight
        padding: UM.Theme.getSize("default_lining").width

        contentItem: ListView {
            clip: true
            implicitHeight: contentHeight
            model: control.popup.visible ? control.delegateModel : null
            currentIndex: control.highlightedIndex

            ScrollIndicator.vertical: ScrollIndicator { }
        }

        background: Rectangle {
            color: UM.Theme.getColor("setting_control")
            border.color: UM.Theme.getColor("setting_control_border")
        }
    }

    delegate: ConfigurationItem
    {
        width: panelWidth - 2 * UM.Theme.getSize("default_lining").width
        height: control.height - 2 * UM.Theme.getSize("default_lining").height
        highlighted: control.highlightedIndex == index
    }
}