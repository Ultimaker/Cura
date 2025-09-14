// Copyright (c) 2019 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3

import UM 1.5 as UM
import Cura 1.1 as Cura


//
// This component contains the content for the "Welcome" page of the welcome on-boarding process.
//
Item
{
    id: base
    UM.I18nCatalog { id: catalog; name: "cura" }

    anchors.left: parent.left
    anchors.right: parent.right
    anchors.top: parent.top

    property int labelWidth: 210 * screenScaleFactor
    property int controlWidth: (UM.Theme.getSize("setting_control").width * 3 / 4) | 0
    property var labelFont: UM.Theme.getFont("default")

    property int columnWidth: ((parent.width - 2 * UM.Theme.getSize("default_margin").width) / 2) | 0
    property int columnSpacing: 3 * screenScaleFactor
    property int propertyStoreIndex: manager ? manager.storeContainerIndex : 1  // definition_changes

    property string extruderStackId: ""
    property int extruderPosition: 0
    property var forceUpdateFunction: manager.forceUpdate

    function updateMaterialDiameter()
    {
        manager.updateMaterialForDiameter(extruderPosition)
    }

    Item
    {
        id: upperBlock
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.margins: UM.Theme.getSize("default_margin").width

        height: childrenRect.height

        // =======================================
        // Left-side column "Nozzle Settings"
        // =======================================
        Column
        {
            anchors.top: parent.top
            anchors.left: parent.left
            width: parent.width / 2

            spacing: base.columnSpacing

            UM.Label   // Title Label
            {
                text: catalog.i18nc("@title:label", "Nozzle Settings")
                font: UM.Theme.getFont("medium_bold")
            }

            Cura.NumericTextFieldWithUnit  // "Nozzle size"
            {
                id: extruderNozzleSizeField
                visible: !Cura.MachineManager.activeMachine.hasVariants
                containerStackId: base.extruderStackId
                settingKey: "machine_nozzle_size"
                settingStoreIndex: propertyStoreIndex
                labelText: catalog.i18nc("@label", "Nozzle size")
                labelFont: base.labelFont
                labelWidth: base.labelWidth
                controlWidth: base.controlWidth
                unitText: catalog.i18nc("@label", "mm")
                forceUpdateOnChangeFunction: forceUpdateFunction
            }

            Cura.NumericTextFieldWithUnit  // "Compatible material diameter"
            {
                id: extruderCompatibleMaterialDiameterField
                containerStackId: base.extruderStackId
                settingKey: "material_diameter"
                settingStoreIndex: propertyStoreIndex
                labelText: catalog.i18nc("@label", "Compatible material diameter")
                labelFont: base.labelFont
                labelWidth: base.labelWidth
                controlWidth: base.controlWidth
                unitText: catalog.i18nc("@label", "mm")
                forceUpdateOnChangeFunction: forceUpdateFunction
                // Other modules won't automatically respond after the user changes the value, so we need to force it.
                afterOnEditingFinishedFunction: updateMaterialDiameter
            }

            Cura.NumericTextFieldWithUnit  // "Nozzle offset X"
            {
                id: extruderNozzleOffsetXField
                containerStackId: base.extruderStackId
                settingKey: "machine_nozzle_offset_x"
                settingStoreIndex: propertyStoreIndex
                labelText: catalog.i18nc("@label", "Nozzle offset X")
                labelFont: base.labelFont
                labelWidth: base.labelWidth
                controlWidth: base.controlWidth
                unitText: catalog.i18nc("@label", "mm")
                minimum: Number.NEGATIVE_INFINITY
                forceUpdateOnChangeFunction: forceUpdateFunction
            }

            Cura.NumericTextFieldWithUnit  // "Nozzle offset Y"
            {
                id: extruderNozzleOffsetYField
                containerStackId: base.extruderStackId
                settingKey: "machine_nozzle_offset_y"
                settingStoreIndex: propertyStoreIndex
                labelText: catalog.i18nc("@label", "Nozzle offset Y")
                labelFont: base.labelFont
                labelWidth: base.labelWidth
                controlWidth: base.controlWidth
                unitText: catalog.i18nc("@label", "mm")
                minimum: Number.NEGATIVE_INFINITY
                forceUpdateOnChangeFunction: forceUpdateFunction
            }

            Cura.NumericTextFieldWithUnit  // "Cooling Fan Number"
            {
                id: extruderNozzleCoolingFanNumberField
                containerStackId: base.extruderStackId
                settingKey: "machine_extruder_cooling_fan_number"
                settingStoreIndex: propertyStoreIndex
                labelText: catalog.i18nc("@label", "Cooling Fan Number")
                labelFont: base.labelFont
                labelWidth: base.labelWidth
                controlWidth: base.controlWidth
                unitText: ""
                decimals: 0
                forceUpdateOnChangeFunction: forceUpdateFunction
            }
        }


        // =======================================
        // Right-side column "Nozzle Settings"
        // =======================================
        Column
        {
            anchors.top: parent.top
            anchors.right: parent.right
            width: parent.width / 2

            spacing: base.columnSpacing

            UM.Label   // Title Label
            {
                text: catalog.i18nc("@title:label", " ")
                font: UM.Theme.getFont("medium_bold")
            }

            Cura.NumericTextFieldWithUnit
            {
                id: extruderChangeDurationFieldId
                containerStackId: base.extruderStackId
                settingKey: "machine_extruder_change_duration"
                settingStoreIndex: propertyStoreIndex
                labelText: catalog.i18nc("@label", "Extruder Change duration")
                labelFont: base.labelFont
                labelWidth: base.labelWidth
                controlWidth: base.controlWidth
                unitText: catalog.i18nc("@label", "s")
                forceUpdateOnChangeFunction: forceUpdateFunction
            }

            Cura.NumericTextFieldWithUnit
            {
                id: extruderStartCodeDurationFieldId
                containerStackId: base.extruderStackId
                settingKey: "machine_extruder_start_code_duration"
                settingStoreIndex: propertyStoreIndex
                labelText: catalog.i18nc("@label", "Extruder Start G-code duration")
                labelFont: base.labelFont
                labelWidth: base.labelWidth
                controlWidth: base.controlWidth
                unitText: catalog.i18nc("@label", "s")
                forceUpdateOnChangeFunction: forceUpdateFunction
            }

            Cura.NumericTextFieldWithUnit
            {
                id: extruderEndCodeDurationFieldId
                containerStackId: base.extruderStackId
                settingKey: "machine_extruder_end_code_duration"
                settingStoreIndex: propertyStoreIndex
                labelText: catalog.i18nc("@label", "Extruder End G-code duration")
                labelFont: base.labelFont
                labelWidth: base.labelWidth
                controlWidth: base.controlWidth
                unitText: catalog.i18nc("@label", "s")
                forceUpdateOnChangeFunction: forceUpdateFunction
            }
        }
    }

    Item  // Extruder Start and End G-code
    {
        id: lowerBlock
        anchors.top: upperBlock.bottom
        anchors.bottom: parent.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.margins: UM.Theme.getSize("default_margin").width

        Column
        {
            anchors.top: parent.top
            anchors.left: parent.left
            anchors.bottom: buttonLearnMore.top
            anchors.bottomMargin: UM.Theme.getSize("default_margin").height
            
            width: parent.width / 2

            spacing: base.columnSpacing

            Cura.GcodeTextArea   // "Extruder Prestart G-code"
            {
                anchors.top: parent.top
                anchors.left: parent.left
                height: (parent.height / 2) - UM.Theme.getSize("default_margin").height
                width: base.columnWidth - UM.Theme.getSize("default_margin").width

                labelText: catalog.i18nc("@title:label", "Extruder Prestart G-code")
                containerStackId: base.extruderStackId
                settingKey: "machine_extruder_prestart_code"
                settingStoreIndex: propertyStoreIndex
            }

            Cura.GcodeTextArea   // "Extruder Start G-code"
            {
                anchors.bottom: parent.bottom
                anchors.left: parent.left
                height: (parent.height / 2) - UM.Theme.getSize("default_margin").height
                width: base.columnWidth - UM.Theme.getSize("default_margin").width

                labelText: catalog.i18nc("@title:label", "Extruder Start G-code")
                containerStackId: base.extruderStackId
                settingKey: "machine_extruder_start_code"
                settingStoreIndex: propertyStoreIndex
            }
        }

        Cura.GcodeTextArea   // "Extruder End G-code"
        {
            anchors.top: parent.top
            anchors.bottom: buttonLearnMore.top
            anchors.bottomMargin: UM.Theme.getSize("default_margin").height
            anchors.right: parent.right
            width: base.columnWidth - UM.Theme.getSize("default_margin").width

            labelText: catalog.i18nc("@title:label", "Extruder End G-code")
            containerStackId: base.extruderStackId
            settingKey: "machine_extruder_end_code"
            settingStoreIndex: propertyStoreIndex
        }

        Cura.TertiaryButton
        {
            id: buttonLearnMore

            text: catalog.i18nc("@button", "Learn more")
            iconSource: UM.Theme.getIcon("LinkExternal")
            isIconOnRightSide: true
            onClicked: Qt.openUrlExternally("https://github.com/Ultimaker/Cura/wiki/Start-End-G%E2%80%90Code")
            anchors.bottom: parent.bottom
            anchors.right: parent.right
        }
    }
}
