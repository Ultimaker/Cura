// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4

import UM 1.2 as UM
import Cura 1.0 as Cura


//
//  Enable support
//
Item
{
    id: enableSupportRow
    height: childrenRect.height

    property real labelColumnWidth: Math.round(width / 3)

    Cura.IconWithText
    {
        id: enableSupportRowTitle
        anchors.top: parent.top
        anchors.left: parent.left
        visible: enableSupportCheckBox.visible
        source: UM.Theme.getIcon("category_support")
        text: catalog.i18nc("@label", "Support")
        font: UM.Theme.getFont("medium")
        width: labelColumnWidth
    }

    Item
    {
        id: enableSupportContainer
        height: enableSupportCheckBox.height

        anchors
        {
            left: enableSupportRowTitle.right
            right: parent.right
            verticalCenter: enableSupportRowTitle.verticalCenter
        }

        CheckBox
        {
            id: enableSupportCheckBox
            anchors.verticalCenter: parent.verticalCenter

            property alias _hovered: enableSupportMouseArea.containsMouse

            style: UM.Theme.styles.checkbox
            enabled: recommendedPrintSetup.settingsEnabled

            visible: supportEnabled.properties.enabled == "True"
            checked: supportEnabled.properties.value == "True"

            MouseArea
            {
                id: enableSupportMouseArea
                anchors.fill: parent
                hoverEnabled: true

                onClicked: supportEnabled.setPropertyValue("value", supportEnabled.properties.value != "True")

                onEntered:
                {
                    base.showTooltip(enableSupportCheckBox, Qt.point(-enableSupportContainer.x - UM.Theme.getSize("thick_margin").width, 0),
                        catalog.i18nc("@label", "Generate structures to support parts of the model which have overhangs. Without these structures, such parts would collapse during printing."))
                }
                onExited: base.hideTooltip()
            }
        }

        ComboBox
        {
            id: supportExtruderCombobox

            height: UM.Theme.getSize("print_setup_big_item").height
            anchors
            {
                left: enableSupportCheckBox.right
                right: parent.right
                leftMargin: UM.Theme.getSize("thick_margin").width
                rightMargin: UM.Theme.getSize("thick_margin").width
                verticalCenter: parent.verticalCenter
            }

            style: UM.Theme.styles.combobox_color
            enabled: recommendedPrintSetup.settingsEnabled
            visible: enableSupportCheckBox.visible && (supportEnabled.properties.value == "True") && (extrudersEnabledCount.properties.value > 1)
            textRole: "text"  // this solves that the combobox isn't populated in the first time Cura is started

            model: extruderModel

            property alias _hovered: supportExtruderMouseArea.containsMouse
            property string color_override: ""  // for manually setting values
            property string color:  // is evaluated automatically, but the first time is before extruderModel being filled
            {
                var current_extruder = extruderModel.get(currentIndex)
                color_override = ""
                if (current_extruder === undefined) return ""
                return (current_extruder.color) ? current_extruder.color : ""
            }

            currentIndex:
            {
                if (supportExtruderNr.properties == null)
                {
                    return Cura.MachineManager.defaultExtruderPosition
                }
                else
                {
                    var extruder = parseInt(supportExtruderNr.properties.value)
                    if ( extruder === -1)
                    {
                        return Cura.MachineManager.defaultExtruderPosition
                    }
                    return extruder;
                }
            }

            onActivated: supportExtruderNr.setPropertyValue("value", String(index))

            MouseArea
            {
                id: supportExtruderMouseArea
                anchors.fill: parent
                hoverEnabled: true
                enabled: recommendedPrintSetup.settingsEnabled
                acceptedButtons: Qt.NoButton
                onEntered:
                {
                    base.showTooltip(supportExtruderCombobox, Qt.point(-enableSupportContainer.x - supportExtruderCombobox.x - UM.Theme.getSize("thick_margin").width, 0),
                        catalog.i18nc("@label", "Select which extruder to use for support. This will build up supporting structures below the model to prevent the model from sagging or printing in mid air."));
                }
                onExited: base.hideTooltip()

            }

            function updateCurrentColor()
            {
                var current_extruder = extruderModel.get(currentIndex)
                if (current_extruder !== undefined)
                {
                    supportExtruderCombobox.color_override = current_extruder.color
                }
            }
        }
    }

    ListModel
    {
        id: extruderModel
        Component.onCompleted: populateExtruderModel()
    }

    //: Model used to populate the extrudelModel
    property var extruders: CuraApplication.getExtrudersModel()
    Connections
    {
        target: extruders
        onModelChanged: populateExtruderModel()
    }

    UM.SettingPropertyProvider
    {
        id: supportEnabled
        containerStack: Cura.MachineManager.activeMachine
        key: "support_enable"
        watchedProperties: [ "value", "enabled", "description" ]
        storeIndex: 0
    }

    UM.SettingPropertyProvider
    {
        id: supportExtruderNr
        containerStack: Cura.MachineManager.activeMachine
        key: "support_extruder_nr"
        watchedProperties: [ "value" ]
        storeIndex: 0
    }

    UM.SettingPropertyProvider
    {
        id: machineExtruderCount
        containerStack: Cura.MachineManager.activeMachine
        key: "machine_extruder_count"
        watchedProperties: ["value"]
        storeIndex: 0
    }

    function populateExtruderModel()
    {
        extruderModel.clear()
        for (var extruderNumber = 0; extruderNumber < extruders.rowCount(); extruderNumber++)
        {
            extruderModel.append({
                text: extruders.getItem(extruderNumber).name,
                color: extruders.getItem(extruderNumber).color
            })
        }
        supportExtruderCombobox.updateCurrentColor()
    }
}