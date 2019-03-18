// Copyright (c) 2019 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3

import UM 1.3 as UM
import Cura 1.1 as Cura

import "../MachineSettings"


//
// This component contains the content for the "Welcome" page of the welcome on-boarding process.
//

Row
{
    id: base
    UM.I18nCatalog { id: catalog; name: "cura" }

    property int labelWidth: 100
    property var labelFont: UM.Theme.getFont("medium")

    // Left-side column for "Printer Settings"
    Column
    {
        spacing: 10

        Label
        {
            text: catalog.i18nc("@title:label", "Printer Settings")
            font: UM.Theme.getFont("medium_bold")
        }

        NumericTextFieldWithUnit  // "X (Width)"
        {
            id: machineXWidthField
            containerStackId: Cura.MachineManager.activeMachineId
            settingKey: "machine_width"
            settingStoreIndex: 1 // TODO
            labelText: catalog.i18nc("@label", "X (Width)")
            labelFont: base.labelFont
            labelWidth: base.labelWidth
            unitText: catalog.i18nc("@label", "mm")
            // TODO: add forceUpdateOnChangeFunction:
        }

        NumericTextFieldWithUnit  // "Y (Depth)"
        {
            id: machineYDepthField
            containerStackId: Cura.MachineManager.activeMachineId
            settingKey: "machine_depth"
            settingStoreIndex: 1 // TODO
            labelText: catalog.i18nc("@label", "Y (Depth)")
            labelFont: base.labelFont
            labelWidth: base.labelWidth
            unitText: catalog.i18nc("@label", "mm")
            // TODO: add forceUpdateOnChangeFunction:
        }

        NumericTextFieldWithUnit  // "Z (Height)"
        {
            id: machineZHeightField
            containerStackId: Cura.MachineManager.activeMachineId
            settingKey: "machine_height"
            settingStoreIndex: 1 // TODO
            labelText: catalog.i18nc("@label", "Z (Height)")
            labelFont: base.labelFont
            labelWidth: base.labelWidth
            unitText: catalog.i18nc("@label", "mm")
            // TODO: add forceUpdateOnChangeFunction:
        }

        ComboBoxWithOptions  // "Build plate shape"
        {
            id: buildPlateShapeComboBox
            containerStackId: Cura.MachineManager.activeMachineId
            settingKey: "machine_shape"
            settingStoreIndex: 1 // TODO
            labelText: catalog.i18nc("@label", "Build plate shape")
            labelWidth: base.labelWidth
            // TODO: add forceUpdateOnChangeFunction:
        }

        SimpleCheckBox  // "Origin at center"
        {
            id: originAtCenterCheckBox
            containerStackId: Cura.MachineManager.activeMachineId
            settingKey: "machine_center_is_zero"
            settingStoreIndex: 1 // TODO
            labelText: catalog.i18nc("@label", "Origin at center")
            labelFont: base.labelFont
            // TODO: add forceUpdateOnChangeFunction:
        }

        SimpleCheckBox  // "Heated bed"
        {
            id: heatedBedCheckBox
            containerStackId: Cura.MachineManager.activeMachineId
            settingKey: "machine_heated_bed"
            settingStoreIndex: 1 // TODO
            labelText: catalog.i18nc("@label", "Heated bed")
            labelFont: base.labelFont
            // TODO: add forceUpdateOnChangeFunction:
        }

        ComboBoxWithOptions  // "G-code flavor"
        {
            id: gcodeFlavorComboBox
            containerStackId: Cura.MachineManager.activeMachineId
            settingKey: "machine_gcode_flavor"
            settingStoreIndex: 1 // TODO
            labelText: catalog.i18nc("@label", "G-code flavor")
            labelFont: base.labelFont
            labelWidth: base.labelWidth
            // TODO: add forceUpdateOnChangeFunction:
            // TODO: add afterOnActivate: manager.updateHasMaterialsMetadata
        }
    }

    // Right-side column for "Printhead Settings"
    Column
    {
        spacing: 10

        Label
        {
            text: catalog.i18nc("@title:label", "Printhead Settings")
            font: UM.Theme.getFont("medium_bold")
        }



    }
}
