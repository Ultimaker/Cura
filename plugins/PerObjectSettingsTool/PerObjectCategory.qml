// Copyright (c) 2022 Ultimaker B.V.
// Uranium is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 2.1

import UM 1.5 as UM
import Cura 1.0 as Cura
import ".."

Button {
    id: base;

    background: Item {}

    contentItem: Row
    {
        spacing: UM.Theme.getSize("default_lining").width

        Item //Wrapper to give space before icon with fixed width. This allows aligning checkbox with category icon.
        {
            height: label.height
            width: height
            anchors.verticalCenter: parent.verticalCenter

            UM.RecolorImage
            {
                anchors.verticalCenter: parent.verticalCenter
                height: (label.height / 2) | 0
                width: height
                source: base.checked ? UM.Theme.getIcon("ChevronSingleDown") : UM.Theme.getIcon("ChevronSingleRight")
                color: base.hovered ? UM.Theme.getColor("primary_button_hover"): UM.Theme.getColor("primary_button_text")
            }
        }
        UM.RecolorImage
        {
            anchors.verticalCenter: parent.verticalCenter
            height: label.height
            width: height
            source: UM.Theme.getIcon(definition.icon)
            color: base.hovered ? UM.Theme.getColor("primary_button_hover") : UM.Theme.getColor("primary_button_text")
        }
        UM.Label
        {
            id: label
            anchors.verticalCenter: parent.verticalCenter
            text: base.text
            color: base.hovered ? UM.Theme.getColor("primary_button_hover") : UM.Theme.getColor("primary_button_text")
            font.bold: true
        }
    }

    signal showTooltip(string text)
    signal hideTooltip()
    signal contextMenuRequested()

    text: definition.label

    checkable: true
    checked: definition.expanded

    onClicked: definition.expanded ? settingDefinitionsModel.collapseRecursive(definition.key) : settingDefinitionsModel.expandRecursive(definition.key)
}
