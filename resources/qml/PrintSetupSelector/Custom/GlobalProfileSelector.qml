// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1
import QtQuick.Layouts 1.2

import UM 1.2 as UM
import Cura 1.0 as Cura

Item
{
    id: globalProfileRow
    height: childrenRect.height

    Label
    {
        id: globalProfileLabel
        anchors
        {
            top: parent.top
            bottom: parent.bottom
            left: parent.left
            right: globalProfileSelection.left
        }
        text: catalog.i18nc("@label", "Profile")
        font: UM.Theme.getFont("medium")
        color: UM.Theme.getColor("text")
        verticalAlignment: Text.AlignVCenter
    }

    ToolButton
    {
        id: globalProfileSelection

        text: generateActiveQualityText()
        width: UM.Theme.getSize("print_setup_big_item").width
        height: UM.Theme.getSize("print_setup_big_item").height
        anchors
        {
            top: parent.top
            right: parent.right
        }
        tooltip: Cura.MachineManager.activeQualityOrQualityChangesName
        style: UM.Theme.styles.print_setup_header_button
        activeFocusOnPress: true
        menu: Cura.ProfileMenu { }

        function generateActiveQualityText()
        {
            var result = Cura.MachineManager.activeQualityOrQualityChangesName
            if (Cura.MachineManager.isActiveQualityExperimental)
            {
                result += " (Experimental)"
            }

            if (Cura.MachineManager.isActiveQualitySupported)
            {
                if (Cura.MachineManager.activeQualityLayerHeight > 0)
                {
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
            width: UM.Theme.getSize("print_setup_icon").width
            height: UM.Theme.getSize("print_setup_icon").height

            anchors.verticalCenter: parent.verticalCenter
            anchors.right: parent.right
            anchors.rightMargin: Math.round(UM.Theme.getSize("setting_preferences_button_margin").width - UM.Theme.getSize("thick_margin").width)

            color: hovered ? UM.Theme.getColor("setting_control_button_hover") : UM.Theme.getColor("setting_control_button");
            iconSource: UM.Theme.getIcon("star")

            onClicked:
            {
                forceActiveFocus();
                Cura.Actions.manageProfiles.trigger()
            }
            onEntered:
            {
                var content = catalog.i18nc("@tooltip","Some setting/override values are different from the values stored in the profile.\n\nClick to open the profile manager.")
                base.showTooltip(globalProfileRow, Qt.point(-UM.Theme.getSize("default_margin").width, 0),  content)
            }
            onExited: base.hideTooltip()
        }
    }
}