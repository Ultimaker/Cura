//Copyright (c) 2022 Ultimaker B.V.
//Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.15
import QtQuick.Controls 2.1

import UM 1.5 as UM
import Cura 1.0 as Cura


Item
{
    property alias color: background.color
    property var extruderModel
    property var position: index
    property var connectedPrinter: Cura.MachineManager.printerOutputDevices.length >= 1 ? Cura.MachineManager.printerOutputDevices[0] : null

    implicitWidth: parent.width
    implicitHeight: UM.Theme.getSize("print_setup_extruder_box").height

    UM.SettingPropertyProvider
    {
        id: extruderTemperature
        containerStackId: Cura.ExtruderManager.extruderIds[position]
        key: "material_print_temperature_layer_0"
        watchedProperties: ["value", "minimum_value", "maximum_value", "resolve"]
        storeIndex: 0
    }

    Rectangle
    {
        id: background
        anchors.fill: parent

        // Extruder name.
        UM.Label
        {
            text: Cura.MachineManager.activeMachine.extruderList[position].name !== "" ? Cura.MachineManager.activeMachine.extruderList[position].name : catalog.i18nc("@label", "Extruder")
            anchors.left: parent.left
            anchors.top: parent.top
            anchors.margins: UM.Theme.getSize("default_margin").width
        }

        // Target temperature.
        UM.Label
        {
            id: extruderTargetTemperature
            text: Math.round(extruderModel.targetHotendTemperature) + "°C"
            font: UM.Theme.getFont("default_bold")
            color: UM.Theme.getColor("text_inactive")
            anchors.right: parent.right
            anchors.rightMargin: UM.Theme.getSize("default_margin").width
            anchors.bottom: extruderCurrentTemperature.bottom

            //For tooltip.
            MouseArea
            {
                id: extruderTargetTemperatureTooltipArea
                hoverEnabled: true
                anchors.fill: parent
                onHoveredChanged:
                {
                    if (containsMouse)
                    {
                        base.showTooltip(
                            base,
                            {x: 0, y: extruderTargetTemperature.mapToItem(base, 0, Math.floor(-parent.height / 4)).y},
                            catalog.i18nc("@tooltip", "The target temperature of the hotend. The hotend will heat up or cool down towards this temperature. If this is 0, the hotend heating is turned off.")
                        );
                    }
                    else
                    {
                        base.hideTooltip();
                    }
                }
            }
        }

        //Temperature indication.
        UM.Label
        {
            id: extruderCurrentTemperature
            text: Math.round(extruderModel.hotendTemperature) + "°C"
            font: UM.Theme.getFont("large_bold")
            anchors.right: extruderTargetTemperature.left
            anchors.top: parent.top
            anchors.margins: UM.Theme.getSize("default_margin").width


            //For tooltip.
            MouseArea
            {
                id: extruderCurrentTemperatureTooltipArea
                hoverEnabled: true
                anchors.fill: parent
                onHoveredChanged:
                {
                    if (containsMouse)
                    {
                        base.showTooltip(
                            base,
                            {x: 0, y: parent.mapToItem(base, 0, Math.floor(-parent.height / 4)).y},
                            catalog.i18nc("@tooltip", "The current temperature of this hotend.")
                        );
                    }
                    else
                    {
                        base.hideTooltip();
                    }
                }
            }
        }

        //Input field for pre-heat temperature.
        Rectangle
        {
            id: preheatTemperatureControl
            color: !enabled ? UM.Theme.getColor("setting_control_disabled") : showError ? UM.Theme.getColor("setting_validation_error_background") : UM.Theme.getColor("setting_validation_ok")
            property var showError:
            {
                if(extruderTemperature.properties.maximum_value != "None" && extruderTemperature.properties.maximum_value <  Math.floor(preheatTemperatureInput.text))
                {
                    return true;
                } else
                {
                    return false;
                }
            }
            enabled:
            {
                if (extruderModel == null)
                {
                    return false; //Can't preheat if not connected.
                }
                if (!connectedPrinter.acceptsCommands)
                {
                    return false; //Not allowed to do anything.
                }
                if (connectedPrinter.activePrinter && connectedPrinter.activePrinter.activePrintJob)
                {
                    if((["printing", "pre_print", "resuming", "pausing", "paused", "error", "offline"]).indexOf(connectedPrinter.activePrinter.activePrintJob.state) != -1)
                    {
                        return false; //Printer is in a state where it can't react to pre-heating.
                    }
                }
                return true;
            }
            border.width: UM.Theme.getSize("default_lining").width
            border.color: !enabled ? UM.Theme.getColor("setting_control_disabled_border") : preheatTemperatureInputMouseArea.containsMouse ? UM.Theme.getColor("setting_control_border_highlight") : UM.Theme.getColor("setting_control_border")
            anchors.right: preheatButton.left
            anchors.rightMargin: UM.Theme.getSize("default_margin").width
            anchors.bottom: parent.bottom
            anchors.bottomMargin: UM.Theme.getSize("default_margin").height
            width: UM.Theme.getSize("monitor_preheat_temperature_control").width
            height: UM.Theme.getSize("monitor_preheat_temperature_control").height
            visible: extruderModel != null ? enabled && extruderModel.canPreHeatHotends && !extruderModel.isPreheating : true
            //Highlight of input field.
            Rectangle
            {
                anchors.fill: parent
                anchors.margins: UM.Theme.getSize("default_lining").width
                color: UM.Theme.getColor("setting_control_highlight")
                opacity: preheatTemperatureControl.hovered ? 1.0 : 0
            }
            //Change cursor on hovering.
            MouseArea
            {
                id: preheatTemperatureInputMouseArea
                hoverEnabled: true
                anchors.fill: parent
                cursorShape: Qt.IBeamCursor

                onHoveredChanged:
                {
                    if (containsMouse)
                    {
                        base.showTooltip(
                            base,
                            {x: 0, y: preheatTemperatureInputMouseArea.mapToItem(base, 0, -parent.height/2).y},
                            catalog.i18nc("@tooltip of temperature input", "The temperature to pre-heat the hotend to.")
                        );
                    }
                    else
                    {
                        base.hideTooltip();
                    }
                }
            }
            UM.Label
            {
                id: unit
                anchors.right: parent.right
                anchors.rightMargin: UM.Theme.getSize("setting_unit_margin").width
                anchors.verticalCenter: parent.verticalCenter

                text: "°C";
                color: UM.Theme.getColor("setting_unit")
            }
            TextInput
            {
                id: preheatTemperatureInput
                font: UM.Theme.getFont("default")
                color: !enabled ? UM.Theme.getColor("setting_control_disabled_text") : UM.Theme.getColor("setting_control_text")
                selectByMouse: true
                maximumLength: 5
                enabled: parent.enabled
                validator: RegularExpressionValidator { regularExpression: /^-?[0-9]{0,9}[.,]?[0-9]{0,10}$/ } //Floating point regex.
                anchors.left: parent.left
                anchors.leftMargin: UM.Theme.getSize("setting_unit_margin").width
                anchors.right: unit.left
                anchors.verticalCenter: parent.verticalCenter
                renderType: Text.NativeRendering

                text:
                {
                    if (!extruderTemperature.properties.value)
                    {
                        return "";
                    }
                    else
                    {
                        return extruderTemperature.properties.value;
                    }
                }
            }
        }

        Cura.SecondaryButton
        {
            id: preheatButton
            height: UM.Theme.getSize("setting_control").height
            visible: extruderModel != null ? extruderModel.canPreHeatHotends: true
            enabled:
            {
                if (!preheatTemperatureControl.enabled)
                {
                    return false; //Not connected, not authenticated or printer is busy.
                }
                if (extruderModel.isPreheating)
                {
                    return true;
                }
                if (extruderTemperature.properties.minimum_value != "None" && Math.floor(preheatTemperatureInput.text) < Math.floor(extruderTemperature.properties.minimum_value))
                {
                    return false; //Target temperature too low.
                }
                if (extruderTemperature.properties.maximum_value != "None" && Math.floor(preheatTemperatureInput.text) > Math.floor(extruderTemperature.properties.maximum_value))
                {
                    return false; //Target temperature too high.
                }
                if (Math.floor(preheatTemperatureInput.text) == 0)
                {
                    return false; //Setting the temperature to 0 is not allowed (since that cancels the pre-heating).
                }
                return true; //Preconditions are met.
            }
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            anchors.margins: UM.Theme.getSize("default_margin").width

            text:
            {
                if(extruderModel == null)
                {
                    return ""
                }
                if(extruderModel.isPreheating )
                {
                    return catalog.i18nc("@button Cancel pre-heating", "Cancel")
                } else
                {
                    return catalog.i18nc("@button", "Pre-heat")
                }
            }

            onClicked:
            {
                if (!extruderModel.isPreheating)
                {
                    extruderModel.preheatHotend(preheatTemperatureInput.text, 900);
                }
                else
                {
                    extruderModel.cancelPreheatHotend();
                }
            }

            onHoveredChanged:
            {
                if (hovered)
                {
                    base.showTooltip(
                        base,
                        {x: 0, y: preheatButton.mapToItem(base, 0, -parent.height).y},
                        catalog.i18nc("@tooltip of pre-heat", "Heat the hotend in advance before printing. You can continue adjusting your print while it is heating, and you won't have to wait for the hotend to heat up when you're ready to print.")
                    );
                }
                else
                {
                    base.hideTooltip();
                }
            }
        }

        //Material colour indication.
        Rectangle
        {
            id: materialColor
            width: Math.floor(materialName.height * 0.75)
            height: Math.floor(materialName.height * 0.75)
            radius: width / 2
            color: extruderModel.activeMaterial ? extruderModel.activeMaterial.color: "#00000000"
            border.width: UM.Theme.getSize("default_lining").width
            border.color: UM.Theme.getColor("lining")
            visible: extruderModel.activeMaterial != null
            anchors.left: parent.left
            anchors.leftMargin: UM.Theme.getSize("default_margin").width
            anchors.verticalCenter: materialName.verticalCenter

            //For tooltip.
            MouseArea
            {
                id: materialColorTooltipArea
                hoverEnabled: true
                anchors.fill: parent
                onHoveredChanged:
                {
                    if (containsMouse)
                    {
                        base.showTooltip(
                            base,
                            {x: 0, y: parent.mapToItem(base, 0, -parent.height / 2).y},
                            catalog.i18nc("@tooltip", "The colour of the material in this extruder.")
                        );
                    }
                    else
                    {
                        base.hideTooltip();
                    }
                }
            }
        }
        //Material name.
        UM.Label
        {
            id: materialName
            text: extruderModel.activeMaterial != null ? extruderModel.activeMaterial.type : ""
            anchors.left: materialColor.right
            anchors.bottom: parent.bottom
            anchors.margins: UM.Theme.getSize("default_margin").width

            //For tooltip.
            MouseArea
            {
                id: materialNameTooltipArea
                hoverEnabled: true
                anchors.fill: parent
                onHoveredChanged:
                {
                    if (containsMouse)
                    {
                        base.showTooltip(
                            base,
                            {x: 0, y: parent.mapToItem(base, 0, 0).y},
                            catalog.i18nc("@tooltip", "The material in this extruder.")
                        );
                    }
                    else
                    {
                        base.hideTooltip();
                    }
                }
            }
        }

        //Variant name.
        UM.Label
        {
            id: variantName
            text: extruderModel.hotendID
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            anchors.margins: UM.Theme.getSize("default_margin").width

            //For tooltip.
            MouseArea
            {
                id: variantNameTooltipArea
                hoverEnabled: true
                anchors.fill: parent
                onHoveredChanged:
                {
                    if (containsMouse)
                    {
                        base.showTooltip(
                            base,
                            { x: 0, y: parent.mapToItem(base, 0, -parent.height / 4).y },
                            catalog.i18nc("@tooltip", "The nozzle inserted in this extruder.")
                        );
                    }
                    else
                    {
                        base.hideTooltip();
                    }
                }
            }
        }
    }
}