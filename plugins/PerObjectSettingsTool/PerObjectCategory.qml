// Copyright (c) 2015 Ultimaker B.V.
// Uranium is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1
import QtQuick.Layouts 1.1

import UM 1.1 as UM

import ".."

Button {
    id: base;

    style: ButtonStyle {
        background: Item { }
        label: Row
        {
            spacing: UM.Theme.getSize("default_lining").width

            UM.RecolorImage
            {
                anchors.verticalCenter: parent.verticalCenter
                height: (label.height / 2) | 0
                width: height
                source: control.checked ? UM.Theme.getIcon("ChevronSingleDown") : UM.Theme.getIcon("ChevronSingleRight");
                color: control.hovered ? palette.highlight : palette.buttonText
            }
            UM.RecolorImage
            {
                anchors.verticalCenter: parent.verticalCenter
                height: label.height
                width: height
                source: control.iconSource
                color: control.hovered ? palette.highlight : palette.buttonText
            }
            Label
            {
                id: label
                anchors.verticalCenter: parent.verticalCenter
                text: control.text
                color: control.hovered ? palette.highlight : palette.buttonText
                font.bold: true
            }

            SystemPalette { id: palette }
        }
    }

    signal showTooltip(string text);
    signal hideTooltip();
    signal contextMenuRequested()

    text: definition.label
    iconSource: UM.Theme.getIcon(definition.icon)

    checkable: true
    checked: definition.expanded

    onClicked: definition.expanded ? settingDefinitionsModel.collapseRecursive(definition.key) : settingDefinitionsModel.expandRecursive(definition.key)
}
