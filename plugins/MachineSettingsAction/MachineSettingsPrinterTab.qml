// Copyright (c) 2019 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.3

import UM 1.5 as UM
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

    property string machineStackId: Cura.MachineManager.activeMachine.id

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

            UM.Label   // Title Label
            {
                text: catalog.i18nc("@title:label", "Printer Settings")
                font: UM.Theme.getFont("medium_bold")
                width: parent.width
                elide: Text.ElideRight
            }

            Cura.NumericTextFieldWithUnit  // "X (Width)"
            {
                id: machineXWidthField
                draftManager: manager
                containerStackId: machineStackId
                settingKey: "machine_width"
                settingStoreIndex: propertyStoreIndex
                labelText: catalog.i18nc("@label", "X (Width)")
                labelFont: base.labelFont
                labelWidth: base.labelWidth
                controlWidth: base.controlWidth
                unitText: catalog.i18nc("@label", "mm")
                maximum: 2000000
            }

            Cura.NumericTextFieldWithUnit  // "Y (Depth)"
            {
                id: machineYDepthField
                draftManager: manager
                containerStackId: machineStackId
                settingKey: "machine_depth"
                settingStoreIndex: propertyStoreIndex
                labelText: catalog.i18nc("@label", "Y (Depth)")
                labelFont: base.labelFont
                labelWidth: base.labelWidth
                controlWidth: base.controlWidth
                unitText: catalog.i18nc("@label", "mm")
                maximum: 2000000
            }

            Cura.NumericTextFieldWithUnit  // "Z (Height)"
            {
                id: machineZHeightField
                draftManager: manager
                containerStackId: machineStackId
                settingKey: "machine_height"
                settingStoreIndex: propertyStoreIndex
                labelText: catalog.i18nc("@label", "Z (Height)")
                labelFont: base.labelFont
                labelWidth: base.labelWidth
                controlWidth: base.controlWidth
                unitText: catalog.i18nc("@label", "mm")
            }

            Cura.ComboBoxWithOptions  // "Build plate shape"
            {
                id: buildPlateShapeComboBox
                draftManager: manager
                containerStackId: machineStackId
                settingKey: "machine_shape"
                settingStoreIndex: propertyStoreIndex
                labelText: catalog.i18nc("@label", "Build plate shape")
                labelFont: base.labelFont
                labelWidth: base.labelWidth
                controlWidth: base.controlWidth
            }

            Cura.SimpleCheckBox  // "Origin at center"
            {
                id: originAtCenterCheckBox
                draftManager: manager
                containerStackId: machineStackId
                settingKey: "machine_center_is_zero"
                settingStoreIndex: propertyStoreIndex
                labelText: catalog.i18nc("@label", "Origin at center")
                labelFont: base.labelFont
                labelWidth: base.labelWidth
            }

            Cura.SimpleCheckBox  // "Heated bed"
            {
                id: heatedBedCheckBox
                draftManager: manager
                containerStackId: machineStackId
                settingKey: "machine_heated_bed"
                settingStoreIndex: propertyStoreIndex
                labelText: catalog.i18nc("@label", "Heated bed")
                labelFont: base.labelFont
                labelWidth: base.labelWidth
            }

            Cura.SimpleCheckBox  // "Heated build volume"
            {
                id: heatedVolumeCheckBox
                draftManager: manager
                containerStackId: machineStackId
                settingKey: "machine_heated_build_volume"
                settingStoreIndex: propertyStoreIndex
                labelText: catalog.i18nc("@label", "Heated build volume")
                labelFont: base.labelFont
                labelWidth: base.labelWidth
            }

            Cura.ComboBoxWithOptions  // "G-code flavor"
            {
                id: gcodeFlavorComboBox
                draftManager: manager
                containerStackId: machineStackId
                settingKey: "machine_gcode_flavor"
                settingStoreIndex: propertyStoreIndex
                labelText: catalog.i18nc("@label", "G-code flavor")
                labelFont: base.labelFont
                labelWidth: base.labelWidth
                controlWidth: base.controlWidth
            }

			Cura.NumericTextFieldWithUnit  // "Print Time Estimation Factor"
            {
                id: machineTimeEstimationFactorField
                draftManager: manager
                containerStackId: machineStackId
                settingKey: "machine_time_estimation_factor"
                settingStoreIndex: propertyStoreIndex
                labelText: catalog.i18nc("@label", "Print Time Estimation Factor")
                labelFont: base.labelFont
                labelWidth: base.labelWidth
                controlWidth: base.controlWidth
                unitText: catalog.i18nc("@label", "%")
                decimals: 1
                minimum: 1
                maximum: 1000
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

            UM.Label   // Title Label
            {
                text: catalog.i18nc("@title:label", "Printhead Settings")
                font: UM.Theme.getFont("medium_bold")
                width: parent.width
                elide: Text.ElideRight
            }

            Cura.PrintHeadMinMaxTextField  // "X min"
            {
                id: machineXMinField
                draftManager: manager

                settingStoreIndex: propertyStoreIndex

                labelText: catalog.i18nc("@label", "X min")
                labelFont: base.labelFont
                labelWidth: base.labelWidth
                controlWidth: base.controlWidth
                unitText: catalog.i18nc("@label", "mm")

                axisName: "x"
                axisMinOrMax: "min"
                minimum: Number.NEGATIVE_INFINITY
                maximum: 0
            }

            Cura.PrintHeadMinMaxTextField  // "Y min"
            {
                id: machineYMinField
                draftManager: manager

                settingStoreIndex: propertyStoreIndex

                labelText: catalog.i18nc("@label", "Y min ( '-' towards back)")
                labelFont: base.labelFont
                labelWidth: base.labelWidth
                controlWidth: base.controlWidth
                unitText: catalog.i18nc("@label", "mm")

                axisName: "y"
                axisMinOrMax: "min"
                minimum: Number.NEGATIVE_INFINITY
                maximum: 0
            }

            Cura.PrintHeadMinMaxTextField  // "X max"
            {
                id: machineXMaxField
                draftManager: manager

                settingStoreIndex: propertyStoreIndex

                labelText: catalog.i18nc("@label", "X max")
                labelFont: base.labelFont
                labelWidth: base.labelWidth
                controlWidth: base.controlWidth
                unitText: catalog.i18nc("@label", "mm")

                axisName: "x"
                axisMinOrMax: "max"
            }

            Cura.PrintHeadMinMaxTextField  // "Y max"
            {
                id: machineYMaxField
                draftManager: manager

                containerStackId: machineStackId
                settingKey: "machine_head_with_fans_polygon"
                settingStoreIndex: propertyStoreIndex

                labelText: catalog.i18nc("@label", "Y max ( '+' towards front)")
                labelFont: base.labelFont
                labelWidth: base.labelWidth
                controlWidth: base.controlWidth
                unitText: catalog.i18nc("@label", "mm")

                axisName: "y"
                axisMinOrMax: "max"
            }

            Cura.NumericTextFieldWithUnit  // "Gantry Height"
            {
                id: machineGantryHeightField
                draftManager: manager
                containerStackId: machineStackId
                settingKey: "gantry_height"
                settingStoreIndex: propertyStoreIndex
                labelText: catalog.i18nc("@label", "Gantry Height")
                labelFont: base.labelFont
                labelWidth: base.labelWidth
                controlWidth: base.controlWidth
                unitText: catalog.i18nc("@label", "mm")
            }

            Cura.ComboBoxWithOptions  // "Number of Extruders"
            {
                id: numberOfExtrudersComboBox
                draftManager: manager
                containerStackId: machineStackId
                settingKey: "machine_extruder_count"
                settingStoreIndex: propertyStoreIndex
                labelText: catalog.i18nc("@label", "Number of Extruders")
                labelFont: base.labelFont
                labelWidth: base.labelWidth
                controlWidth: base.controlWidth

                optionModel: ListModel
                {
                    id: extruderCountModel

                    Component.onCompleted:
                    {
                        updateModel();
                    }

                    function updateModel()
                    {
                        clear();
                        for (var i = 1; i <= Cura.MachineManager.activeMachine.maxExtruderCount; i ++) {
                            // Use String as value. JavaScript only has Number. PropertyProvider.setPropertyValue()
                            // takes a QVariant as value, and Number gets translated into a float. This will cause problem
                            // for integer settings such as "Number of Extruders".
                            append({ text: String(i), value: String(i) });
                        }
                    }
                }

                Connections
                {
                    target: Cura.MachineManager
                    function onGlobalContainerChanged() {
                        extruderCountModel.updateModel();
                    }
                }
            }

            /* 
               - Fix for this issue: https://github.com/Ultimaker/Cura/issues/9167 
               - Allows user to toggle if GCODE coordinates are affected by the extruder offset. 
               - Machine wide setting. CuraEngine/src/gcodeExport.cpp is not set up to evaluate per extruder currently.
               - If it is moved to per-extruder (unlikely), then this should be moved to the extruder tab.
            */
            Cura.SimpleCheckBox  // "GCode Affected By Extruder Offsets"
            {
                id: applyExtruderOffsetsCheckbox
                draftManager: manager
                containerStackId: machineStackId
                settingKey: "machine_use_extruder_offset_to_offset_coords"
                settingStoreIndex: propertyStoreIndex
                labelText: catalog.i18nc("@label", "Apply Extruder offsets to GCode")
                labelFont: base.labelFont
                labelWidth: base.labelWidth
            }

            /* 
               - Allows user to toggle if Start Gcode is the absolute first gcode.
            */
            Cura.SimpleCheckBox  // "Make sure Start Code is before all gcodes"
            {
                id: applyStartGcodeFirstCheckbox
                draftManager: manager
                containerStackId: machineStackId
                settingKey: "machine_start_gcode_first"
                settingStoreIndex: propertyStoreIndex
                labelText: catalog.i18nc("@label", "Start GCode must be first")
                labelFont: base.labelFont
                labelWidth: base.labelWidth
            }
			
			
            /* The "Shared Heater" feature is temporarily disabled because its
            implementation is incomplete. Printers with multiple filaments going
            into one nozzle will keep the inactive filaments retracted at the
            start of a print. However CuraEngine assumes that all filaments
            start at the nozzle tip. So it'll start printing the second filament
            without unretracting it.
            See: https://github.com/Ultimaker/Cura/issues/8148

            Cura.SimpleCheckBox  // "Shared Heater"
            {
                id: sharedHeaterCheckBox
                draftManager: manager
                containerStackId: machineStackId
                settingKey: "machine_extruders_share_heater"
                settingStoreIndex: propertyStoreIndex
                labelText: catalog.i18nc("@label", "Shared Heater")
                labelFont: base.labelFont
                labelWidth: base.labelWidth
            }
            */
        }
    }

    RowLayout  // Start and End G-code
    {
        id: lowerBlock
        spacing: UM.Theme.getSize("default_margin").width
        anchors
        {
            top: upperBlock.bottom
            bottom: buttonLearnMore.top
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
            draftManager: manager
            settingStoreIndex: propertyStoreIndex
        }

        Cura.GcodeTextArea   // "End G-code"
        {
            Layout.fillWidth: true
            Layout.fillHeight: true

            labelText: catalog.i18nc("@title:label", "End G-code")
            containerStackId: machineStackId
            settingKey: "machine_end_gcode"
            draftManager: manager
            settingStoreIndex: propertyStoreIndex
        }

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
        anchors.margins: UM.Theme.getSize("default_margin").width
    }
}
