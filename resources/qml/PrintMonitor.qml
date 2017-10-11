// Copyright (c) 2017 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1
import QtQuick.Layouts 1.1

import UM 1.2 as UM
import Cura 1.0 as Cura

Column
{
    id: printMonitor
    property var connectedPrinter: Cura.MachineManager.printerOutputDevices.length >= 1 ? Cura.MachineManager.printerOutputDevices[0] : null

    Cura.ExtrudersModel
    {
        id: extrudersModel
        simpleNames: true
    }

    Rectangle
    {
        id: connectedPrinterHeader
        width: parent.width
        height: Math.floor(childrenRect.height + UM.Theme.getSize("default_margin").height * 2)
        color: UM.Theme.getColor("setting_category")

        Label
        {
            id: connectedPrinterNameLabel
            font: UM.Theme.getFont("large")
            color: UM.Theme.getColor("text")
            anchors.left: parent.left
            anchors.top: parent.top
            anchors.margins: UM.Theme.getSize("default_margin").width
            text: connectedPrinter != null ? connectedPrinter.name : catalog.i18nc("@info:status", "No printer connected")
        }
        Label
        {
            id: connectedPrinterAddressLabel
            text: (connectedPrinter != null && connectedPrinter.address != null) ? connectedPrinter.address : ""
            font: UM.Theme.getFont("small")
            color: UM.Theme.getColor("text_inactive")
            anchors.top: parent.top
            anchors.right: parent.right
            anchors.margins: UM.Theme.getSize("default_margin").width
        }
        Label
        {
            text: connectedPrinter != null ? connectedPrinter.connectionText : catalog.i18nc("@info:status", "The printer is not connected.")
            color: connectedPrinter != null && connectedPrinter.acceptsCommands ? UM.Theme.getColor("setting_control_text") : UM.Theme.getColor("setting_control_disabled_text")
            font: UM.Theme.getFont("very_small")
            wrapMode: Text.WordWrap
            anchors.left: parent.left
            anchors.leftMargin: UM.Theme.getSize("default_margin").width
            anchors.right: parent.right
            anchors.rightMargin: UM.Theme.getSize("default_margin").width
            anchors.top: connectedPrinterNameLabel.bottom
        }
    }

    Rectangle
    {
        color: UM.Theme.getColor("sidebar_lining")
        width: parent.width
        height: childrenRect.height

        Flow
        {
            id: extrudersGrid
            spacing: UM.Theme.getSize("sidebar_lining_thin").width
            width: parent.width

            Repeater
            {
                id: extrudersRepeater
                model: machineExtruderCount.properties.value

                delegate: Rectangle
                {
                    id: extruderRectangle
                    color: UM.Theme.getColor("sidebar")
                    width: index == machineExtruderCount.properties.value - 1 && index % 2 == 0 ? extrudersGrid.width : Math.floor(extrudersGrid.width / 2 - UM.Theme.getSize("sidebar_lining_thin").width / 2)
                    height: UM.Theme.getSize("sidebar_extruder_box").height

                    Label //Extruder name.
                    {
                        text: ExtruderManager.getExtruderName(index) != "" ? ExtruderManager.getExtruderName(index) : catalog.i18nc("@label", "Extruder")
                        color: UM.Theme.getColor("text")
                        font: UM.Theme.getFont("default")
                        anchors.left: parent.left
                        anchors.top: parent.top
                        anchors.margins: UM.Theme.getSize("default_margin").width
                    }

                    Label //Target temperature.
                    {
                        id: extruderTargetTemperature
                        text: (connectedPrinter != null && connectedPrinter.hotendIds[index] != null && connectedPrinter.targetHotendTemperatures[index] != null) ? Math.round(connectedPrinter.targetHotendTemperatures[index]) + "°C" : ""
                        font: UM.Theme.getFont("small")
                        color: UM.Theme.getColor("text_inactive")
                        anchors.right: parent.right
                        anchors.rightMargin: UM.Theme.getSize("default_margin").width
                        anchors.bottom: extruderTemperature.bottom

                        MouseArea //For tooltip.
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
                                        {x: 0, y: extruderTargetTemperature.mapToItem(base, 0, -parent.height / 4).y},
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
                    Label //Temperature indication.
                    {
                        id: extruderTemperature
                        text: (connectedPrinter != null && connectedPrinter.hotendIds[index] != null && connectedPrinter.hotendTemperatures[index] != null) ? Math.round(connectedPrinter.hotendTemperatures[index]) + "°C" : ""
                        color: UM.Theme.getColor("text")
                        font: UM.Theme.getFont("large")
                        anchors.right: extruderTargetTemperature.left
                        anchors.top: parent.top
                        anchors.margins: UM.Theme.getSize("default_margin").width

                        MouseArea //For tooltip.
                        {
                            id: extruderTemperatureTooltipArea
                            hoverEnabled: true
                            anchors.fill: parent
                            onHoveredChanged:
                            {
                                if (containsMouse)
                                {
                                    base.showTooltip(
                                        base,
                                        {x: 0, y: parent.mapToItem(base, 0, -parent.height / 4).y},
                                        catalog.i18nc("@tooltip", "The current temperature of this extruder.")
                                    );
                                }
                                else
                                {
                                    base.hideTooltip();
                                }
                            }
                        }
                    }
                    Rectangle //Material colour indication.
                    {
                        id: materialColor
                        width: Math.floor(materialName.height * 0.75)
                        height: Math.floor(materialName.height * 0.75)
                        radius: width / 2
                        color: (connectedPrinter != null && connectedPrinter.materialColors[index] != null && connectedPrinter.materialIds[index] != "") ? connectedPrinter.materialColors[index] : "#00000000"
                        border.width: UM.Theme.getSize("default_lining").width
                        border.color: UM.Theme.getColor("lining")
                        visible: connectedPrinter != null && connectedPrinter.materialColors[index] != null && connectedPrinter.materialIds[index] != ""
                        anchors.left: parent.left
                        anchors.leftMargin: UM.Theme.getSize("default_margin").width
                        anchors.verticalCenter: materialName.verticalCenter

                        MouseArea //For tooltip.
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
                    Label //Material name.
                    {
                        id: materialName
                        text: (connectedPrinter != null && connectedPrinter.materialNames[index] != null && connectedPrinter.materialIds[index] != "") ? connectedPrinter.materialNames[index] : ""
                        font: UM.Theme.getFont("default")
                        color: UM.Theme.getColor("text")
                        anchors.left: materialColor.right
                        anchors.bottom: parent.bottom
                        anchors.margins: UM.Theme.getSize("default_margin").width

                        MouseArea //For tooltip.
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
                    Label //Variant name.
                    {
                        id: variantName
                        text: (connectedPrinter != null && connectedPrinter.hotendIds[index] != null) ? connectedPrinter.hotendIds[index] : ""
                        font: UM.Theme.getFont("default")
                        color: UM.Theme.getColor("text")
                        anchors.right: parent.right
                        anchors.bottom: parent.bottom
                        anchors.margins: UM.Theme.getSize("default_margin").width

                        MouseArea //For tooltip.
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
                                        {x: 0, y: parent.mapToItem(base, 0, -parent.height / 4).y},
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
        }
    }

    Rectangle
    {
        color: UM.Theme.getColor("sidebar_lining")
        width: parent.width
        height: UM.Theme.getSize("sidebar_lining_thin").width
    }

    Rectangle
    {
        color: UM.Theme.getColor("sidebar")
        width: parent.width
        height: machineHeatedBed.properties.value == "True" ? UM.Theme.getSize("sidebar_extruder_box").height : 0
        visible: machineHeatedBed.properties.value == "True"

        Label //Build plate label.
        {
            text: catalog.i18nc("@label", "Build plate")
            font: UM.Theme.getFont("default")
            color: UM.Theme.getColor("text")
            anchors.left: parent.left
            anchors.top: parent.top
            anchors.margins: UM.Theme.getSize("default_margin").width
        }
        Label //Target temperature.
        {
            id: bedTargetTemperature
            text: connectedPrinter != null ? connectedPrinter.targetBedTemperature + "°C" : ""
            font: UM.Theme.getFont("small")
            color: UM.Theme.getColor("text_inactive")
            anchors.right: parent.right
            anchors.rightMargin: UM.Theme.getSize("default_margin").width
            anchors.bottom: bedCurrentTemperature.bottom

            MouseArea //For tooltip.
            {
                id: bedTargetTemperatureTooltipArea
                hoverEnabled: true
                anchors.fill: parent
                onHoveredChanged:
                {
                    if (containsMouse)
                    {
                        base.showTooltip(
                            base,
                            {x: 0, y: bedTargetTemperature.mapToItem(base, 0, -parent.height / 4).y},
                            catalog.i18nc("@tooltip", "The target temperature of the heated bed. The bed will heat up or cool down towards this temperature. If this is 0, the bed heating is turned off.")
                        );
                    }
                    else
                    {
                        base.hideTooltip();
                    }
                }
            }
        }
        Label //Current temperature.
        {
            id: bedCurrentTemperature
            text: connectedPrinter != null ? connectedPrinter.bedTemperature + "°C" : ""
            font: UM.Theme.getFont("large")
            color: UM.Theme.getColor("text")
            anchors.right: bedTargetTemperature.left
            anchors.top: parent.top
            anchors.margins: UM.Theme.getSize("default_margin").width

            MouseArea //For tooltip.
            {
                id: bedTemperatureTooltipArea
                hoverEnabled: true
                anchors.fill: parent
                onHoveredChanged:
                {
                    if (containsMouse)
                    {
                        base.showTooltip(
                            base,
                            {x: 0, y: bedCurrentTemperature.mapToItem(base, 0, -parent.height / 4).y},
                            catalog.i18nc("@tooltip", "The current temperature of the heated bed.")
                        );
                    }
                    else
                    {
                        base.hideTooltip();
                    }
                }
            }
        }
        Rectangle //Input field for pre-heat temperature.
        {
            id: preheatTemperatureControl
            color: !enabled ? UM.Theme.getColor("setting_control_disabled") : showError ? UM.Theme.getColor("setting_validation_error_background") : UM.Theme.getColor("setting_validation_ok")
            property var showError:
            {
                if(bedTemperature.properties.maximum_value != "None" && bedTemperature.properties.maximum_value <  Math.floor(preheatTemperatureInput.text))
                {
                    return true;
                } else
                {
                    return false;
                }
            }
            enabled:
            {
                if (connectedPrinter == null)
                {
                    return false; //Can't preheat if not connected.
                }
                if (!connectedPrinter.acceptsCommands)
                {
                    return false; //Not allowed to do anything.
                }
                if (connectedPrinter.jobState == "printing" || connectedPrinter.jobState == "pre_print" || connectedPrinter.jobState == "resuming" || connectedPrinter.jobState == "pausing" || connectedPrinter.jobState == "paused" || connectedPrinter.jobState == "error" || connectedPrinter.jobState == "offline")
                {
                    return false; //Printer is in a state where it can't react to pre-heating.
                }
                return true;
            }
            border.width: UM.Theme.getSize("default_lining").width
            border.color: !enabled ? UM.Theme.getColor("setting_control_disabled_border") : preheatTemperatureInputMouseArea.containsMouse ? UM.Theme.getColor("setting_control_border_highlight") : UM.Theme.getColor("setting_control_border")
            anchors.left: parent.left
            anchors.leftMargin: UM.Theme.getSize("default_margin").width
            anchors.bottom: parent.bottom
            anchors.bottomMargin: UM.Theme.getSize("default_margin").height
            width: UM.Theme.getSize("setting_control").width
            height: UM.Theme.getSize("setting_control").height
            visible: connectedPrinter != null ? connectedPrinter.canPreHeatBed: true
            Rectangle //Highlight of input field.
            {
                anchors.fill: parent
                anchors.margins: UM.Theme.getSize("default_lining").width
                color: UM.Theme.getColor("setting_control_highlight")
                opacity: preheatTemperatureControl.hovered ? 1.0 : 0
            }
            Label //Maximum temperature indication.
            {
                text: (bedTemperature.properties.maximum_value != "None" ? bedTemperature.properties.maximum_value : "") + "°C"
                color: UM.Theme.getColor("setting_unit")
                font: UM.Theme.getFont("default")
                anchors.right: parent.right
                anchors.rightMargin: UM.Theme.getSize("setting_unit_margin").width
                anchors.verticalCenter: parent.verticalCenter
            }
            MouseArea //Change cursor on hovering.
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
                            {x: 0, y: preheatTemperatureInputMouseArea.mapToItem(base, 0, 0).y},
                            catalog.i18nc("@tooltip of temperature input", "The temperature to pre-heat the bed to.")
                        );
                    }
                    else
                    {
                        base.hideTooltip();
                    }
                }
            }
            TextInput
            {
                id: preheatTemperatureInput
                font: UM.Theme.getFont("default")
                color: !enabled ? UM.Theme.getColor("setting_control_disabled_text") : UM.Theme.getColor("setting_control_text")
                selectByMouse: true
                maximumLength: 10
                enabled: parent.enabled
                validator: RegExpValidator { regExp: /^-?[0-9]{0,9}[.,]?[0-9]{0,10}$/ } //Floating point regex.
                anchors.left: parent.left
                anchors.leftMargin: UM.Theme.getSize("setting_unit_margin").width
                anchors.right: parent.right
                anchors.verticalCenter: parent.verticalCenter

                Component.onCompleted:
                {
                    if (!bedTemperature.properties.value)
                    {
                        text = "";
                    }
                    if ((bedTemperature.resolve != "None" && bedTemperature.resolve) && (bedTemperature.stackLevels[0] != 0) && (bedTemperature.stackLevels[0] != 1))
                    {
                        // We have a resolve function. Indicates that the setting is not settable per extruder and that
                        // we have to choose between the resolved value (default) and the global value
                        // (if user has explicitly set this).
                        text = bedTemperature.resolve;
                    }
                    else
                    {
                        text = bedTemperature.properties.value;
                    }
                }
            }
        }

        UM.RecolorImage
        {
            id: preheatCountdownIcon
            width: UM.Theme.getSize("save_button_specs_icons").width
            height: UM.Theme.getSize("save_button_specs_icons").height
            sourceSize.width: width
            sourceSize.height: height
            color: UM.Theme.getColor("text")
            visible: preheatCountdown.visible
            source: UM.Theme.getIcon("print_time")
            anchors.right: preheatCountdown.left
            anchors.rightMargin: Math.floor(UM.Theme.getSize("default_margin").width / 2)
            anchors.verticalCenter: preheatCountdown.verticalCenter
        }

        Timer
        {
            id: preheatUpdateTimer
            interval: 100 //Update every 100ms. You want to update every 1s, but then you have one timer for the updating running out of sync with the actual date timer and you might skip seconds.
            running: connectedPrinter != null && connectedPrinter.preheatBedRemainingTime != ""
            repeat: true
            onTriggered: update()
            property var endTime: new Date() //Set initial endTime to be the current date, so that the endTime has initially already passed and the timer text becomes invisible if you were to update.
            function update()
            {
                preheatCountdown.text = ""
                if (connectedPrinter != null)
                {
                    preheatCountdown.text = connectedPrinter.preheatBedRemainingTime;
                }
                if (preheatCountdown.text == "") //Either time elapsed or not connected.
                {
                    stop();
                }
            }
        }
        Label
        {
            id: preheatCountdown
            text: connectedPrinter != null ? connectedPrinter.preheatBedRemainingTime : ""
            visible: text != "" //Has no direct effect, but just so that we can link visibility of clock icon to visibility of the countdown text.
            font: UM.Theme.getFont("default")
            color: UM.Theme.getColor("text")
            anchors.right: preheatButton.left
            anchors.rightMargin: UM.Theme.getSize("default_margin").width
            anchors.verticalCenter: preheatButton.verticalCenter
        }

        Button //The pre-heat button.
        {
            id: preheatButton
            height: UM.Theme.getSize("setting_control").height
            visible: connectedPrinter != null ? connectedPrinter.canPreHeatBed: true
            enabled:
            {
                if (!preheatTemperatureControl.enabled)
                {
                    return false; //Not connected, not authenticated or printer is busy.
                }
                if (preheatUpdateTimer.running)
                {
                    return true; //Can always cancel if the timer is running.
                }
                if (bedTemperature.properties.minimum_value != "None" && Math.floor(preheatTemperatureInput.text) < Math.floor(bedTemperature.properties.minimum_value))
                {
                    return false; //Target temperature too low.
                }
                if (bedTemperature.properties.maximum_value != "None" && Math.floor(preheatTemperatureInput.text) > Math.floor(bedTemperature.properties.maximum_value))
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
            style: ButtonStyle {
                background: Rectangle
                {
                    border.width: UM.Theme.getSize("default_lining").width
                    implicitWidth: actualLabel.contentWidth + (UM.Theme.getSize("default_margin").width * 2)
                    border.color:
                    {
                        if(!control.enabled)
                        {
                            return UM.Theme.getColor("action_button_disabled_border");
                        }
                        else if(control.pressed)
                        {
                            return UM.Theme.getColor("action_button_active_border");
                        }
                        else if(control.hovered)
                        {
                            return UM.Theme.getColor("action_button_hovered_border");
                        }
                        else
                        {
                            return UM.Theme.getColor("action_button_border");
                        }
                    }
                    color:
                    {
                        if(!control.enabled)
                        {
                            return UM.Theme.getColor("action_button_disabled");
                        }
                        else if(control.pressed)
                        {
                            return UM.Theme.getColor("action_button_active");
                        }
                        else if(control.hovered)
                        {
                            return UM.Theme.getColor("action_button_hovered");
                        }
                        else
                        {
                            return UM.Theme.getColor("action_button");
                        }
                    }
                    Behavior on color
                    {
                        ColorAnimation
                        {
                            duration: 50
                        }
                    }

                    Label
                    {
                        id: actualLabel
                        anchors.centerIn: parent
                        color:
                        {
                            if(!control.enabled)
                            {
                                return UM.Theme.getColor("action_button_disabled_text");
                            }
                            else if(control.pressed)
                            {
                                return UM.Theme.getColor("action_button_active_text");
                            }
                            else if(control.hovered)
                            {
                                return UM.Theme.getColor("action_button_hovered_text");
                            }
                            else
                            {
                                return UM.Theme.getColor("action_button_text");
                            }
                        }
                        font: UM.Theme.getFont("action_button")
                        text: preheatUpdateTimer.running ? catalog.i18nc("@button Cancel pre-heating", "Cancel") : catalog.i18nc("@button", "Pre-heat")
                    }
                }
            }

            onClicked:
            {
                if (!preheatUpdateTimer.running)
                {
                    connectedPrinter.preheatBed(preheatTemperatureInput.text, connectedPrinter.preheatBedTimeout);
                    preheatUpdateTimer.start();
                    preheatUpdateTimer.update(); //Update once before the first timer is triggered.
                }
                else
                {
                    connectedPrinter.cancelPreheatBed();
                    preheatUpdateTimer.update();
                }
            }

            onHoveredChanged:
            {
                if (hovered)
                {
                    base.showTooltip(
                        base,
                        {x: 0, y: preheatButton.mapToItem(base, 0, 0).y},
                        catalog.i18nc("@tooltip of pre-heat", "Heat the bed in advance before printing. You can continue adjusting your print while it is heating, and you won't have to wait for the bed to heat up when you're ready to print.")
                    );
                }
                else
                {
                    base.hideTooltip();
                }
            }
        }
    }

    UM.SettingPropertyProvider
    {
        id: bedTemperature
        containerStackId: Cura.MachineManager.activeMachineId
        key: "material_bed_temperature"
        watchedProperties: ["value", "minimum_value", "maximum_value", "resolve"]
        storeIndex: 0

        property var resolve: Cura.MachineManager.activeStackId != Cura.MachineManager.activeMachineId ? properties.resolve : "None"
    }

    UM.SettingPropertyProvider
    {
        id: machineExtruderCount
        containerStackId: Cura.MachineManager.activeMachineId
        key: "machine_extruder_count"
        watchedProperties: ["value"]
    }

    Loader
    {
        sourceComponent: monitorSection
        property string label: catalog.i18nc("@label", "Active print")
    }
    Loader
    {
        sourceComponent: monitorItem
        property string label: catalog.i18nc("@label", "Job Name")
        property string value: connectedPrinter != null ? connectedPrinter.jobName : ""
    }
    Loader
    {
        sourceComponent: monitorItem
        property string label: catalog.i18nc("@label", "Printing Time")
        property string value: connectedPrinter != null ? getPrettyTime(connectedPrinter.timeTotal) : ""
    }
    Loader
    {
        sourceComponent: monitorItem
        property string label: catalog.i18nc("@label", "Estimated time left")
        property string value: connectedPrinter != null ? getPrettyTime(connectedPrinter.timeTotal - connectedPrinter.timeElapsed) : ""
        visible: connectedPrinter != null && (connectedPrinter.jobState == "printing" || connectedPrinter.jobState == "resuming" || connectedPrinter.jobState == "pausing" || connectedPrinter.jobState == "paused")
    }

    Component
    {
        id: monitorItem

        Row
        {
            height: UM.Theme.getSize("setting_control").height
            width: Math.floor(base.width - 2 * UM.Theme.getSize("default_margin").width)
            anchors.left: parent.left
            anchors.leftMargin: UM.Theme.getSize("default_margin").width

            Label
            {
                width: Math.floor(parent.width * 0.4)
                anchors.verticalCenter: parent.verticalCenter
                text: label
                color: connectedPrinter != null && connectedPrinter.acceptsCommands ? UM.Theme.getColor("setting_control_text") : UM.Theme.getColor("setting_control_disabled_text")
                font: UM.Theme.getFont("default")
                elide: Text.ElideRight
            }
            Label
            {
                width: Math.floor(parent.width * 0.6)
                anchors.verticalCenter: parent.verticalCenter
                text: value
                color: connectedPrinter != null && connectedPrinter.acceptsCommands ? UM.Theme.getColor("setting_control_text") : UM.Theme.getColor("setting_control_disabled_text")
                font: UM.Theme.getFont("default")
                elide: Text.ElideRight
            }
        }
    }
    Component
    {
        id: monitorSection

        Rectangle
        {
            color: UM.Theme.getColor("setting_category")
            width: base.width
            height: UM.Theme.getSize("section").height

            Label
            {
                anchors.verticalCenter: parent.verticalCenter
                anchors.left: parent.left
                anchors.leftMargin: UM.Theme.getSize("default_margin").width
                text: label
                font: UM.Theme.getFont("setting_category")
                color: UM.Theme.getColor("setting_category_text")
            }
        }
    }
}