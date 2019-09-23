// Copyright (c) 2019 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.3

import UM 1.3 as UM
import Cura 1.1 as Cura


//
// This the content in the "Printer" tab in the Machine Settings dialog.
//
Item
{
    id: base
    UM.I18nCatalog { id: catalog; name: "cura" }

    property int columnWidth: ((parent.width - 2 * UM.Theme.getSize("default_margin").width) / 2) | 0
    property int columnSpacing: 3 * screenScaleFactor
    property int propertyStoreIndex: manager ? manager.storeContainerIndex : 1  // definition_changes

    property int labelWidth: (columnWidth * 2 / 3 - UM.Theme.getSize("default_margin").width * 2) | 0
    property int controlWidth: (columnWidth / 3) | 0
    property var labelFont: UM.Theme.getFont("default")

    property string machineStackId: Cura.MachineManager.activeMachineId

    property var forceUpdateFunction: manager.forceUpdate

    RowLayout
    {
        id: upperBlock
        anchors
        {
            top: parent.top
            left: parent.left
            right: parent.right
            margins: UM.Theme.getSize("default_margin").width
        }
        spacing: UM.Theme.getSize("default_margin").width
        
        // =======================================
        // Left-side column for "Printer Settings"
        // =======================================
        Column
        {
            Layout.fillWidth: true
            Layout.alignment: Qt.AlignTop

            spacing: base.columnSpacing

            Label   // Title Label
            {
                text: catalog.i18nc("@title:label", "Printer Settings")
                font: UM.Theme.getFont("medium_bold")
                color: UM.Theme.getColor("text")
                renderType: Text.NativeRendering
                width: parent.width
                elide: Text.ElideRight
            }

            Cura.NumericTextFieldWithUnit  // "X (Width)"
            {
                id: machineXWidthField
                containerStackId: machineStackId
                settingKey: "machine_width"
                settingStoreIndex: propertyStoreIndex
                labelText: catalog.i18nc("@label", "X (Width)")
                labelFont: base.labelFont
                labelWidth: base.labelWidth
                controlWidth: base.controlWidth
                unitText: catalog.i18nc("@label", "mm")
                forceUpdateOnChangeFunction: forceUpdateFunction
            }

            Cura.NumericTextFieldWithUnit  // "Y (Depth)"
            {
                id: machineYDepthField
                containerStackId: machineStackId
                settingKey: "machine_depth"
                settingStoreIndex: propertyStoreIndex
                labelText: catalog.i18nc("@label", "Y (Depth)")
                labelFont: base.labelFont
                labelWidth: base.labelWidth
                controlWidth: base.controlWidth
                unitText: catalog.i18nc("@label", "mm")
                forceUpdateOnChangeFunction: forceUpdateFunction
            }

            Cura.NumericTextFieldWithUnit  // "Z (Height)"
            {
                id: machineZHeightField
                containerStackId: machineStackId
                settingKey: "machine_height"
                settingStoreIndex: propertyStoreIndex
                labelText: catalog.i18nc("@label", "Z (Height)")
                labelFont: base.labelFont
                labelWidth: base.labelWidth
                controlWidth: base.controlWidth
                unitText: catalog.i18nc("@label", "mm")
                forceUpdateOnChangeFunction: forceUpdateFunction
            }

            Cura.ComboBoxWithOptions  // "Build plate shape"
            {
                id: buildPlateShapeComboBox
                containerStackId: machineStackId
                settingKey: "machine_shape"
                settingStoreIndex: propertyStoreIndex
                labelText: catalog.i18nc("@label", "Build plate shape")
                labelFont: base.labelFont
                labelWidth: base.labelWidth
                controlWidth: base.controlWidth
                forceUpdateOnChangeFunction: forceUpdateFunction
            }

            Cura.SimpleCheckBox  // "Origin at center"
            {
                id: originAtCenterCheckBox
                containerStackId: machineStackId
                settingKey: "machine_center_is_zero"
                settingStoreIndex: propertyStoreIndex
                labelText: catalog.i18nc("@label", "Origin at center")
                labelFont: base.labelFont
                labelWidth: base.labelWidth
                forceUpdateOnChangeFunction: forceUpdateFunction
            }

            Cura.SimpleCheckBox  // "Heated bed"
            {
                id: heatedBedCheckBox
                containerStackId: machineStackId
                settingKey: "machine_heated_bed"
                settingStoreIndex: propertyStoreIndex
                labelText: catalog.i18nc("@label", "Heated bed")
                labelFont: base.labelFont
                labelWidth: base.labelWidth
                forceUpdateOnChangeFunction: forceUpdateFunction
            }

            Cura.SimpleCheckBox  // "Heated build volume"
            {
                id: heatedVolumeCheckBox
                containerStackId: machineStackId
                settingKey: "machine_heated_build_volume"
                settingStoreIndex: propertyStoreIndex
                labelText: catalog.i18nc("@label", "Heated build volume")
                labelFont: base.labelFont
                labelWidth: base.labelWidth
                forceUpdateOnChangeFunction: forceUpdateFunction
            }

            Cura.ComboBoxWithOptions  // "G-code flavor"
            {
                id: gcodeFlavorComboBox
                containerStackId: machineStackId
                settingKey: "machine_gcode_flavor"
                settingStoreIndex: propertyStoreIndex
                labelText: catalog.i18nc("@label", "G-code flavor")
                labelFont: base.labelFont
                labelWidth: base.labelWidth
                controlWidth: base.controlWidth
                forceUpdateOnChangeFunction: forceUpdateFunction
                // FIXME(Lipu): better document this.
                // This has something to do with UM2 and UM2+ regarding "has_material" and the gcode flavor settings.
                // I don't remember exactly what.
                afterOnEditingFinishedFunction: manager.updateHasMaterialsMetadata
            }
        }

        // =======================================
        // Right-side column for "Printhead Settings"
        // =======================================
        Column
        {
            Layout.fillWidth: true
            Layout.alignment: Qt.AlignTop

            spacing: base.columnSpacing

            Label   // Title Label
            {
                text: catalog.i18nc("@title:label", "Printhead Settings")
                font: UM.Theme.getFont("medium_bold")
                color: UM.Theme.getColor("text")
                renderType: Text.NativeRendering
                width: parent.width
                elide: Text.ElideRight
            }

            Cura.PrintHeadMinMaxTextField  // "X min"
            {
                id: machineXMinField

                settingStoreIndex: propertyStoreIndex

                labelText: catalog.i18nc("@label", "X min")
                labelFont: base.labelFont
                labelWidth: base.labelWidth
                controlWidth: base.controlWidth
                unitText: catalog.i18nc("@label", "mm")

                axisName: "x"
                axisMinOrMax: "min"
                allowNegativeValue: true
                allowPositiveValue: false

                forceUpdateOnChangeFunction: forceUpdateFunction
            }

            Cura.PrintHeadMinMaxTextField  // "Y min"
            {
                id: machineYMinField

                settingStoreIndex: propertyStoreIndex

                labelText: catalog.i18nc("@label", "Y min")
                labelFont: base.labelFont
                labelWidth: base.labelWidth
                controlWidth: base.controlWidth
                unitText: catalog.i18nc("@label", "mm")

                axisName: "y"
                axisMinOrMax: "min"
                allowNegativeValue: true
                allowPositiveValue: false

                forceUpdateOnChangeFunction: forceUpdateFunction
            }

            Cura.PrintHeadMinMaxTextField  // "X max"
            {
                id: machineXMaxField

                settingStoreIndex: propertyStoreIndex

                labelText: catalog.i18nc("@label", "X max")
                labelFont: base.labelFont
                labelWidth: base.labelWidth
                controlWidth: base.controlWidth
                unitText: catalog.i18nc("@label", "mm")

                axisName: "x"
                axisMinOrMax: "max"
                allowNegativeValue: false
                allowPositiveValue: true

                forceUpdateOnChangeFunction: forceUpdateFunction
            }

            Cura.PrintHeadMinMaxTextField  // "Y max"
            {
                id: machineYMaxField

                containerStackId: machineStackId
                settingKey: "machine_head_with_fans_polygon"
                settingStoreIndex: propertyStoreIndex

                labelText: catalog.i18nc("@label", "Y max")
                labelFont: base.labelFont
                labelWidth: base.labelWidth
                controlWidth: base.controlWidth
                unitText: catalog.i18nc("@label", "mm")

                axisName: "y"
                axisMinOrMax: "max"
                allowNegativeValue: false
                allowPositiveValue: true

                forceUpdateOnChangeFunction: forceUpdateFunction
            }

            Cura.NumericTextFieldWithUnit  // "Gantry Height"
            {
                id: machineGantryHeightField
                containerStackId: machineStackId
                settingKey: "gantry_height"
                settingStoreIndex: propertyStoreIndex
                labelText: catalog.i18nc("@label", "Gantry Height")
                labelFont: base.labelFont
                labelWidth: base.labelWidth
                controlWidth: base.controlWidth
                unitText: catalog.i18nc("@label", "mm")
                forceUpdateOnChangeFunction: forceUpdateFunction
            }

            Cura.ComboBoxWithOptions  // "Number of Extruders"
            {
                id: numberOfExtrudersComboBox
                containerStackId: machineStackId
                settingKey: "machine_extruder_count"
                settingStoreIndex: propertyStoreIndex
                labelText: catalog.i18nc("@label", "Number of Extruders")
                labelFont: base.labelFont
                labelWidth: base.labelWidth
                controlWidth: base.controlWidth
                forceUpdateOnChangeFunction: forceUpdateFunction
                // FIXME(Lipu): better document this.
                // This has something to do with UM2 and UM2+ regarding "has_material" and the gcode flavor settings.
                // I don't remember exactly what.
                afterOnEditingFinishedFunction: manager.updateHasMaterialsMetadata
                setValueFunction: manager.setMachineExtruderCount

                optionModel: ListModel
                {
                    id: extruderCountModel

                    Component.onCompleted:
                    {
                        update()
                    }

                    function update()
                    {
                        clear()
                        for (var i = 1; i <= Cura.MachineManager.activeMachine.maxExtruderCount; i++)
                        {
                            // Use String as value. JavaScript only has Number. PropertyProvider.setPropertyValue()
                            // takes a QVariant as value, and Number gets translated into a float. This will cause problem
                            // for integer settings such as "Number of Extruders".
                            append({ text: String(i), value: String(i) })
                        }
                    }
                }

                Connections
                {
                    target: Cura.MachineManager
                    onGlobalContainerChanged: extruderCountModel.update()
                }
            }
        }
    }

    RowLayout  // Start and End G-code
    {
        id: lowerBlock
        spacing: UM.Theme.getSize("default_margin").width
        anchors
        {
            top: upperBlock.bottom
            bottom: parent.bottom
            left: parent.left
            right: parent.right
            margins: UM.Theme.getSize("default_margin").width
        }

        Cura.GcodeTextArea   // "Start G-code"
        {
            Layout.fillWidth: true
            Layout.fillHeight: true

            labelText: catalog.i18nc("@title:label", "Start G-code")
            containerStackId: machineStackId
            settingKey: "machine_start_gcode"
            settingStoreIndex: propertyStoreIndex
        }

        Cura.GcodeTextArea   // "End G-code"
        {
            Layout.fillWidth: true
            Layout.fillHeight: true

            labelText: catalog.i18nc("@title:label", "End G-code")
            containerStackId: machineStackId
            settingKey: "machine_end_gcode"
            settingStoreIndex: propertyStoreIndex
        }
    }
}
