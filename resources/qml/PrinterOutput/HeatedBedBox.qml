import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1
import QtQuick.Layouts 1.1

import UM 1.2 as UM
import Cura 1.0 as Cura

Item
{
    implicitWidth: parent.width
    height: visible ? UM.Theme.getSize("sidebar_extruder_box").height : 0
    property var printerModel
    Rectangle
    {
        color: UM.Theme.getColor("sidebar")
        anchors.fill: parent

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
            text: printerModel != null ? printerModel.targetBedTemperature + "°C" : ""
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
            text: printerModel != null ? printerModel.bedTemperature + "°C" : ""
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
                if (printerModel == null)
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
            visible: printerModel != null ? printerModel.canPreHeatBed: true
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
                renderType: Text.NativeRendering

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
            running: printerModel != null && printerModel.preheatBedRemainingTime != ""
            repeat: true
            onTriggered: update()
            property var endTime: new Date() //Set initial endTime to be the current date, so that the endTime has initially already passed and the timer text becomes invisible if you were to update.
            function update()
            {
                if(printerModel != null && !printerModel.canPreHeatBed)
                {
                    return // Nothing to do, printer cant preheat at all!
                }
                preheatCountdown.text = ""
                if (printerModel != null)
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
            text: printerModel != null ? printerModel.preheatBedRemainingTime : ""
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
            visible: printerModel != null ? printerModel.canPreHeatBed: true
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
                    printerModel.preheatBed(preheatTemperatureInput.text, printerModel.preheatBedTimeout);
                    preheatUpdateTimer.start();
                    preheatUpdateTimer.update(); //Update once before the first timer is triggered.
                }
                else
                {
                    printerModel.cancelPreheatBed();
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
}