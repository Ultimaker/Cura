import QtQuick 2.10
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.3


Column
{
    spacing: UM.Theme.getSize("default_margin").height

    Row
    {
        width: parent.width
        spacing: UM.Theme.getSize("default_margin").height

        Column
        {
            width: settingsTabs.columnWidth
            spacing: UM.Theme.getSize("default_lining").height

            Label
            {
                text: catalog.i18nc("@label", "Printer Settings")
                font.bold: true
                renderType: Text.NativeRendering
            }

            Item { width: UM.Theme.getSize("default_margin").width; height: UM.Theme.getSize("default_margin").height }

            Loader
            {
                id: buildAreaWidthField
                sourceComponent: numericTextFieldWithUnit
                property string settingKey: "machine_width"
                property string label: catalog.i18nc("@label", "X (Width)")
                property string unit: catalog.i18nc("@label", "mm")
                property bool forceUpdateOnChange: true
            }

            Loader
            {
                id: buildAreaDepthField
                sourceComponent: numericTextFieldWithUnit
                property string settingKey: "machine_depth"
                property string label: catalog.i18nc("@label", "Y (Depth)")
                property string unit: catalog.i18nc("@label", "mm")
                property bool forceUpdateOnChange: true
            }

            Loader
            {
                id: buildAreaHeightField
                sourceComponent: numericTextFieldWithUnit
                property string settingKey: "machine_height"
                property string label: catalog.i18nc("@label", "Z (Height)")
                property string unit: catalog.i18nc("@label", "mm")
                property bool forceUpdateOnChange: true
            }

            Item { width: UM.Theme.getSize("default_margin").width; height: UM.Theme.getSize("default_margin").height }

            Loader
            {
                id: shapeComboBox
                sourceComponent: comboBoxWithOptions
                property string settingKey: "machine_shape"
                property string label: catalog.i18nc("@label", "Build plate shape")
                property bool forceUpdateOnChange: true
            }

            Loader
            {
                id: centerIsZeroCheckBox
                sourceComponent: simpleCheckBox
                property string settingKey: "machine_center_is_zero"
                property string label: catalog.i18nc("@option:check", "Origin at center")
                property bool forceUpdateOnChange: true
            }
            Loader
            {
                id: heatedBedCheckBox
                sourceComponent: simpleCheckBox
                property var settingKey: "machine_heated_bed"
                property string label: catalog.i18nc("@option:check", "Heated bed")
                property bool forceUpdateOnChange: true
            }

            Item { width: UM.Theme.getSize("default_margin").width; height: UM.Theme.getSize("default_margin").height }

            Loader
            {
                id: gcodeFlavorComboBox
                sourceComponent: comboBoxWithOptions
                property string settingKey: "machine_gcode_flavor"
                property string label: catalog.i18nc("@label", "G-code flavor")
                property bool forceUpdateOnChange: true
                property var afterOnActivate: manager.updateHasMaterialsMetadata
            }
        }

        Column
        {
            width: settingsTabs.columnWidth
            spacing: UM.Theme.getSize("default_lining").height

            Label
            {
                text: catalog.i18nc("@label", "Printhead Settings")
                font.bold: true
                renderType: Text.NativeRendering
            }

            Item { width: UM.Theme.getSize("default_margin").width; height: UM.Theme.getSize("default_margin").height }

            Loader
            {
                id: printheadXMinField
                sourceComponent: headPolygonTextField
                property string label: catalog.i18nc("@label", "X min")
                property string tooltip: catalog.i18nc("@tooltip", "Distance from the left of the printhead to the center of the nozzle. Used to prevent colissions between previous prints and the printhead when printing \"One at a Time\".")
                property string axis: "x"
                property string side: "min"
            }

            Loader
            {
                id: printheadYMinField
                sourceComponent: headPolygonTextField
                property string label: catalog.i18nc("@label", "Y min")
                property string tooltip: catalog.i18nc("@tooltip", "Distance from the front of the printhead to the center of the nozzle. Used to prevent colissions between previous prints and the printhead when printing \"One at a Time\".")
                property string axis: "y"
                property string side: "min"
            }

            Loader
            {
                id: printheadXMaxField
                sourceComponent: headPolygonTextField
                property string label: catalog.i18nc("@label", "X max")
                property string tooltip: catalog.i18nc("@tooltip", "Distance from the right of the printhead to the center of the nozzle. Used to prevent colissions between previous prints and the printhead when printing \"One at a Time\".")
                property string axis: "x"
                property string side: "max"
            }

            Loader
            {
                id: printheadYMaxField
                sourceComponent: headPolygonTextField
                property string label: catalog.i18nc("@label", "Y max")
                property string tooltip: catalog.i18nc("@tooltip", "Distance from the rear of the printhead to the center of the nozzle. Used to prevent colissions between previous prints and the printhead when printing \"One at a Time\".")
                property string axis: "y"
                property string side: "max"
            }

            Item { width: UM.Theme.getSize("default_margin").width; height: UM.Theme.getSize("default_margin").height }

            Loader
            {
                id: gantryHeightField
                sourceComponent: numericTextFieldWithUnit
                property string settingKey: "gantry_height"
                property string label: catalog.i18nc("@label", "Gantry height")
                property string unit: catalog.i18nc("@label", "mm")
                property string tooltip: catalog.i18nc("@tooltip", "The height difference between the tip of the nozzle and the gantry system (X and Y axes). Used to prevent collisions between previous prints and the gantry when printing \"One at a Time\".")
                property bool forceUpdateOnChange: true
            }

            Item { width: UM.Theme.getSize("default_margin").width; height: UM.Theme.getSize("default_margin").height }

            UM.TooltipArea
            {
                height: childrenRect.height
                width: childrenRect.width
                text: machineExtruderCountProvider.properties.description
                visible: extruderCountModel.count >= 2

                Row
                {
                    spacing: UM.Theme.getSize("default_margin").width

                    Label
                    {
                        anchors.verticalCenter: extruderCountComboBox.verticalCenter
                        width: Math.max(0, settingsTabs.labelColumnWidth)
                        text: catalog.i18nc("@label", "Number of Extruders")
                        elide: Text.ElideRight
                        renderType: Text.NativeRendering
                    }
                    ComboBox
                    {
                        id: extruderCountComboBox
                        model: ListModel
                        {
                            id: extruderCountModel
                            Component.onCompleted:
                            {
                                for(var i = 0; i < manager.definedExtruderCount; i++)
                                {
                                    extruderCountModel.append({text: String(i + 1), value: i})
                                }
                            }
                        }

                        Connections
                        {
                            target: manager
                            onDefinedExtruderCountChanged:
                            {
                                extruderCountModel.clear();
                                for(var i = 0; i < manager.definedExtruderCount; ++i)
                                {
                                    extruderCountModel.append({text: String(i + 1), value: i});
                                }
                            }
                        }

                        currentIndex: machineExtruderCountProvider.properties.value - 1
                        onActivated:
                        {
                            manager.setMachineExtruderCount(index + 1);
                        }
                    }
                }
            }
        }
    }

    Row
    {
        spacing: UM.Theme.getSize("default_margin").width
        anchors.left: parent.left
        anchors.right: parent.right
        height: parent.height - y
        Column
        {
            height: parent.height
            width: settingsTabs.columnWidth
            Label
            {
                text: catalog.i18nc("@label", "Start G-code")
                font.bold: true
            }
            Loader
            {
                id: machineStartGcodeField
                sourceComponent: gcodeTextArea
                property int areaWidth: parent.width
                property int areaHeight: parent.height - y
                property string settingKey: "machine_start_gcode"
                property string tooltip: catalog.i18nc("@tooltip", "G-code commands to be executed at the very start.")
            }
        }

        Column {
            height: parent.height
            width: settingsTabs.columnWidth
            Label
            {
                text: catalog.i18nc("@label", "End G-code")
                font.bold: true
            }
            Loader
            {
                id: machineEndGcodeField
                sourceComponent: gcodeTextArea
                property int areaWidth: parent.width
                property int areaHeight: parent.height - y
                property string settingKey: "machine_end_gcode"
                property string tooltip: catalog.i18nc("@tooltip", "G-code commands to be executed at the very end.")
            }
        }
    }
}
