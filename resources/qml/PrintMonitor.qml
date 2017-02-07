// Copyright (c) 2017 Ultimaker B.V.
// Cura is released under the terms of the AGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1
import QtQuick.Layouts 1.1

import UM 1.2 as UM
import Cura 1.0 as Cura

Column
{
    id: printMonitor
    property var connectedPrinter: printerConnected ? Cura.MachineManager.printerOutputDevices[0] : null

    Cura.ExtrudersModel
    {
        id: extrudersModel
        simpleNames: true
    }

    Rectangle
    {
        id: connectedPrinterHeader
        width: parent.width
        height: childrenRect.height + UM.Theme.getSize("default_margin").height * 2
        color: UM.Theme.getColor("setting_category")

        Label
        {
            id: connectedPrinterNameLabel
            text: printerConnected ? connectedPrinter.name : catalog.i18nc("@info:status", "No printer connected")
            font: UM.Theme.getFont("large")
            color: UM.Theme.getColor("text")
            anchors.left: parent.left
            anchors.leftMargin: UM.Theme.getSize("default_margin").width
            anchors.top: parent.top
            anchors.topMargin: UM.Theme.getSize("default_margin").height
            anchors.right: parent.right
            anchors.rightMargin: UM.Theme.getSize("default_margin").width
        }
        Label
        {
            id: connectedPrinterAddressLabel
            text: printerConnected ? connectedPrinter.address : ""
            font: UM.Theme.getFont("small")
            color: UM.Theme.getColor("text_inactive")
            anchors.left: parent.left
            anchors.leftMargin: UM.Theme.getSize("default_margin").width
            anchors.top: parent.top
            anchors.topMargin: UM.Theme.getSize("default_margin").height
            anchors.right: parent.right
            anchors.rightMargin: UM.Theme.getSize("default_margin").width
            horizontalAlignment: Text.AlignRight
        }
        Label
        {
            text: printerConnected ? connectedPrinter.connectionText : catalog.i18nc("@info:status", "The printer is not connected.")
            color: printerConnected && printerAcceptsCommands ? UM.Theme.getColor("setting_control_text") : UM.Theme.getColor("setting_control_disabled_text")
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

        GridLayout
        {
            id: extrudersGrid
            columns: 2
            columnSpacing: UM.Theme.getSize("sidebar_lining_thin").width
            rowSpacing: UM.Theme.getSize("sidebar_lining_thin").height
            width: parent.width

            Repeater
            {
                model: machineExtruderCount.properties.value
                delegate: Rectangle
                {
                    id: extruderRectangle
                    color: UM.Theme.getColor("sidebar")
                    width: extrudersGrid.width / 2 - UM.Theme.getSize("sidebar_lining_thin").width / 2
                    height: UM.Theme.getSize("sidebar_extruder_box").height

                    Text //Extruder name.
                    {
                        text: machineExtruderCount.properties.value > 1 ? extrudersModel.getItem(index).name : catalog.i18nc("@label", "Hotend")
                        color: UM.Theme.getColor("text")
                        anchors.left: parent.left
                        anchors.leftMargin: UM.Theme.getSize("default_margin").width
                        anchors.top: parent.top
                        anchors.topMargin: UM.Theme.getSize("default_margin").height
                    }
                    Text //Temperature indication.
                    {
                        text: printerConnected ? Math.round(connectedPrinter.hotendTemperatures[index]) + "°C" : ""
                        font: UM.Theme.getFont("large")
                        anchors.right: parent.right
                        anchors.rightMargin: UM.Theme.getSize("default_margin").width
                        anchors.top: parent.top
                        anchors.topMargin: UM.Theme.getSize("default_margin").height
                    }
                    Rectangle //Material colour indication.
                    {
                        id: materialColor
                        width: materialName.height * 0.75
                        height: materialName.height * 0.75
                        color: printerConnected ? connectedPrinter.materialColors[index] : "#00000000" //Need to check for printerConnected or materialColors[index] gives an error.
                        border.width: UM.Theme.getSize("default_lining").width
                        border.color: UM.Theme.getColor("lining")
                        visible: printerConnected
                        anchors.left: parent.left
                        anchors.leftMargin: UM.Theme.getSize("default_margin").width
                        anchors.verticalCenter: materialName.verticalCenter
                    }
                    Text //Material name.
                    {
                        id: materialName
                        text: printerConnected ? connectedPrinter.materialNames[index] : ""
                        font: UM.Theme.getFont("default")
                        color: UM.Theme.getColor("text")
                        anchors.left: materialColor.right
                        anchors.leftMargin: UM.Theme.getSize("setting_unit_margin").width
                        anchors.bottom: parent.bottom
                        anchors.bottomMargin: UM.Theme.getSize("default_margin").height
                    }
                    Text //Variant name.
                    {
                        text: printerConnected ? connectedPrinter.hotendIds[index] : ""
                        font: UM.Theme.getFont("default")
                        color: UM.Theme.getColor("text")
                        anchors.right: parent.right
                        anchors.rightMargin: UM.Theme.getSize("default_margin").width
                        anchors.bottom: parent.bottom
                        anchors.bottomMargin: UM.Theme.getSize("default_margin").height
                    }
                }
            }
        }
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
            anchors.leftMargin: UM.Theme.getSize("default_margin").width
            anchors.top: parent.top
            anchors.topMargin: UM.Theme.getSize("default_margin").height
        }
        Text //Target temperature.
        {
            id: bedTargetTemperature
            text: printerConnected ? connectedPrinter.targetBedTemperature + "°C" : ""
            font: UM.Theme.getFont("small")
            color: UM.Theme.getColor("text_inactive")
            anchors.right: parent.right
            anchors.rightMargin: UM.Theme.getSize("default_margin").width
            anchors.bottom: bedCurrentTemperature.bottom
        }
        Text //Current temperature.
        {
            id: bedCurrentTemperature
            text: printerConnected ? connectedPrinter.bedTemperature + "°C" : ""
            font: UM.Theme.getFont("large")
            color: UM.Theme.getColor("text")
            anchors.right: bedTargetTemperature.left
            anchors.rightMargin: UM.Theme.getSize("setting_unit_margin").width
            anchors.top: parent.top
            anchors.topMargin: UM.Theme.getSize("default_margin").height
        }
        Rectangle //Input field for pre-heat temperature.
        {
            id: preheatTemperatureControl
            color: UM.Theme.getColor("setting_validation_ok")
            border.width: UM.Theme.getSize("default_lining").width
            border.color: mouseArea.containsMouse ? UM.Theme.getColor("setting_control_border_highlight") : UM.Theme.getColor("setting_control_border")
            anchors.left: parent.left
            anchors.leftMargin: UM.Theme.getSize("default_margin").width
            anchors.bottom: parent.bottom
            anchors.bottomMargin: UM.Theme.getSize("default_margin").height
            width: UM.Theme.getSize("setting_control").width
            height: UM.Theme.getSize("setting_control").height

            Rectangle //Highlight of input field.
            {
                anchors.fill: parent
                anchors.margins: UM.Theme.getSize("default_lining").width
                color: UM.Theme.getColor("setting_control_highlight")
                opacity: preheatTemperatureControl.hovered ? 1.0 : 0
            }
            Label //Maximum temperature indication.
            {
                text: bedTemperature.properties.maximum_value
                color: UM.Theme.getColor("setting_unit")
                font: UM.Theme.getFont("default")
                anchors.right: parent.right
                anchors.rightMargin: UM.Theme.getSize("setting_unit_margin").width
                anchors.verticalCenter: parent.verticalCenter
            }
            MouseArea //Change cursor on hovering.
            {
                id: mouseArea
                hoverEnabled: true
                anchors.fill: parent
                cursorShape: Qt.IBeamCursor
            }
            TextInput
            {
                id: preheatTemperatureInput
                font: UM.Theme.getFont("default")
                color: UM.Theme.getColor("setting_control_text")
                selectByMouse: true
                maximumLength: 10
                validator: RegExpValidator { regExp: /^-?[0-9]{0,9}[.,]?[0-9]{0,10}$/ } //Floating point regex.
                anchors.left: parent.left
                anchors.leftMargin: UM.Theme.getSize("setting_unit_margin").width
                anchors.right: parent.right
                anchors.verticalCenter: parent.verticalCenter

                Binding
                {
                    target: preheatTemperatureInput
                    property: "text"
                    value:
                    {
                        // Stacklevels
                        // 0: user  -> unsaved change
                        // 1: quality changes  -> saved change
                        // 2: quality
                        // 3: material  -> user changed material in materialspage
                        // 4: variant
                        // 5: machine_changes
                        // 6: machine
                        if ((bedTemperature.resolve != "None" && bedTemperature.resolve) && (bedTemperature.stackLevels[0] != 0) && (bedTemperature.stackLevels[0] != 1))
                        {
                            // We have a resolve function. Indicates that the setting is not settable per extruder and that
                            // we have to choose between the resolved value (default) and the global value
                            // (if user has explicitly set this).
                            return bedTemperature.resolve;
                        }
                        else
                        {
                            return bedTemperature.properties.value;
                        }
                    }
                    when: !preheatTemperatureInput.activeFocus
                }
            }
        }

        Timer
        {
            id: preheatCountdownTimer
            interval: 100 //Update every 100ms. You want to update every 1s, but then you have one timer for the updating running out of sync with the actual date timer and you might skip seconds.
            running: false
            repeat: true
            onTriggered: update()
            property var endTime: new Date() //Set initial endTime to be the current date, so that the endTime has initially already passed and the timer text becomes invisible if you were to update.
            function update()
            {
                var now = new Date();
                if (now.getTime() < endTime.getTime())
                {
                    var remaining = endTime - now; //This is in milliseconds.
                    var minutes = Math.floor(remaining / 60 / 1000);
                    var seconds = Math.floor((remaining / 1000) % 60);
                    preheatCountdown.text = minutes + ":" + (seconds < 10 ? "0" + seconds : seconds);
                    preheatCountdown.visible = true;
                }
                else
                {
                    preheatCountdown.visible = false;
                    running = false;
                }
            }
        }
        Text
        {
            id: preheatCountdown
            text: "0:00"
            visible: false //It only becomes visible when the timer is running.
            font: UM.Theme.getFont("default")
            color: UM.Theme.getColor("text")
            anchors.right: preheatButton.left
            anchors.rightMargin: UM.Theme.getSize("default_margin").width
            anchors.verticalCenter: preheatButton.verticalCenter
        }

        Button //The pre-heat button.
        {
            id: preheatButton
            text: catalog.i18nc("@button", "Pre-heat")
            tooltip: catalog.i18nc("@tooltip of pre-heat", "Heat the bed in advance before printing. You can continue adjusting your print while it is heating, and you won't have to wait for the bed to heat up when you're ready to print.")
            height: UM.Theme.getSize("setting_control").height
            enabled: printerConnected
            anchors.right: parent.right
            anchors.rightMargin: UM.Theme.getSize("default_margin").width
            anchors.bottom: parent.bottom
            anchors.bottomMargin: UM.Theme.getSize("default_margin").height
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
                        text: control.text;
                    }
                }
                label: Item
                {
                }
            }

            onClicked:
            {
                connectedPrinter.preheatBed(preheatTemperatureInput.text, 900);
                var now = new Date();
                var end_time = new Date();
                end_time.setTime(now.getTime() + connectedPrinter.preheatBedTimeout * 1000); //*1000 because time is in milliseconds here.
                preheatCountdownTimer.endTime = end_time;
                preheatCountdownTimer.start();
                preheatCountdownTimer.update(); //Update once before the first timer is triggered.
            }
        }
    }

    UM.SettingPropertyProvider
    {
        id: bedTemperature
        containerStackId: Cura.MachineManager.activeMachineId
        key: "material_bed_temperature"
        watchedProperties: ["value", "minimum_value", "maximum_value", "minimum_value_warning", "maximum_value_warning", "resolve"]
        storeIndex: 0

        property var resolve: Cura.MachineManager.activeStackId != Cura.MachineManager.activeMachineId ? properties.resolve : "None"
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
        property string value: printerConnected ? connectedPrinter.jobName : ""
    }
    Loader
    {
        sourceComponent: monitorItem
        property string label: catalog.i18nc("@label", "Printing Time")
        property string value: printerConnected ? getPrettyTime(connectedPrinter.timeTotal) : ""
    }
    Loader
    {
        sourceComponent: monitorItem
        property string label: catalog.i18nc("@label", "Estimated time left")
        property string value: printerConnected ? getPrettyTime(connectedPrinter.timeTotal - connectedPrinter.timeElapsed) : ""
    }

    Component
    {
        id: monitorItem

        Row
        {
            height: UM.Theme.getSize("setting_control").height
            width: base.width - 2 * UM.Theme.getSize("default_margin").width
            anchors.left: parent.left
            anchors.leftMargin: UM.Theme.getSize("default_margin").width

            Label
            {
                width: parent.width * 0.4
                anchors.verticalCenter: parent.verticalCenter
                text: label
                color: printerConnected && printerAcceptsCommands ? UM.Theme.getColor("setting_control_text") : UM.Theme.getColor("setting_control_disabled_text")
                font: UM.Theme.getFont("default")
                elide: Text.ElideRight
            }
            Label
            {
                width: parent.width * 0.6
                anchors.verticalCenter: parent.verticalCenter
                text: value
                color: printerConnected && printerAcceptsCommands ? UM.Theme.getColor("setting_control_text") : UM.Theme.getColor("setting_control_disabled_text")
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
            width: base.width - 2 * UM.Theme.getSize("default_margin").width
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