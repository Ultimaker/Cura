// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1
import QtQuick.Layouts 1.2

import UM 1.2 as UM
import Cura 1.0 as Cura

import "Menus"

Item
{
    id: globalProfileRow
    height: UM.Theme.getSize("print_setup_item").height

    Label
    {
        id: globalProfileLabel
        text: catalog.i18nc("@label","Profile:")
        textFormat: Text.PlainText
        width: Math.round(parent.width * 0.45 - UM.Theme.getSize("thick_margin").width - 2)
        font: UM.Theme.getFont("default")
        color: UM.Theme.getColor("text")
        verticalAlignment: Text.AlignVCenter
        anchors.top: parent.top
        anchors.bottom: parent.bottom
    }

    ToolButton
    {
        id: globalProfileSelection

        text: generateActiveQualityText()
        width: Math.round(parent.width * 0.55)
        height: UM.Theme.getSize("setting_control").height
        anchors.left: globalProfileLabel.right
        anchors.right: parent.right
        tooltip: Cura.MachineManager.activeQualityOrQualityChangesName
        style: UM.Theme.styles.sidebar_header_button
        activeFocusOnPress: true
        menu: ProfileMenu { }

        function generateActiveQualityText () {
            var result = Cura.MachineManager.activeQualityOrQualityChangesName;

            if (Cura.MachineManager.isActiveQualitySupported) {
                if (Cura.MachineManager.activeQualityLayerHeight > 0) {
                    result += " <font color=\"" + UM.Theme.getColor("text_detail") + "\">"
                    result += " - "
                    result += Cura.MachineManager.activeQualityLayerHeight + "mm"
                    result += "</font>"
                }
            }

            return result
        }

        UM.SimpleButton
        {
            id: customisedSettings

            visible: Cura.MachineManager.hasUserSettings
            height: Math.round(parent.height * 0.6)
            width: Math.round(parent.height * 0.6)

            anchors.verticalCenter: parent.verticalCenter
            anchors.right: parent.right
            anchors.rightMargin: Math.round(UM.Theme.getSize("setting_preferences_button_margin").width - UM.Theme.getSize("thick_margin").width)

            color: hovered ? UM.Theme.getColor("setting_control_button_hover") : UM.Theme.getColor("setting_control_button");
            iconSource: UM.Theme.getIcon("star");

            onClicked:
            {
                forceActiveFocus();
                Cura.Actions.manageProfiles.trigger()
            }
            onEntered:
            {
                var content = catalog.i18nc("@tooltip","Some setting/override values are different from the values stored in the profile.\n\nClick to open the profile manager.")
                base.showTooltip(globalProfileRow, Qt.point(-UM.Theme.getSize("thick_margin").width, 0),  content)
            }
            onExited: base.hideTooltip()
        }
    }
}