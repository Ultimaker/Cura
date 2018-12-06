// Copyright (c) 2017 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1
import QtQuick.Layouts 1.1

import UM 1.2 as UM
import Cura 1.0 as Cura

Item
{
    property var printerModel
    property var activePrintJob: printerModel != null ? printerModel.activePrintJob : null
    implicitWidth: parent.width
    implicitHeight: childrenRect.height

    Component
    {
        id: monitorButtonStyle

        ButtonStyle
        {
            background: Rectangle
            {
                border.width: UM.Theme.getSize("default_lining").width
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
                    return UM.Theme.getColor("action_button_border");
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
                    return UM.Theme.getColor("action_button");
                }
                Behavior on color
                {
                    ColorAnimation
                    {
                        duration: 50
                    }
                }
            }

            label: Item
            {
                UM.RecolorImage
                {
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.horizontalCenter: parent.horizontalCenter
                    width: Math.floor(control.width / 2)
                    height: Math.floor(control.height / 2)
                    sourceSize.width: width
                    sourceSize.height: width
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
                        return UM.Theme.getColor("action_button_text");
                    }
                    source: control.iconSource
                }
            }
        }
    }

    Column
    {
        enabled:
        {
            if (printerModel == null)
            {
                return false; //Can't control the printer if not connected
            }

            if (!connectedDevice.acceptsCommands)
            {
                return false; //Not allowed to do anything.
            }

            if(activePrintJob == null)
            {
                return true
            }

            if (activePrintJob.state == "printing" || activePrintJob.state == "resuming" || activePrintJob.state == "pausing" || activePrintJob.state == "error" || activePrintJob.state == "offline")
            {
                return false; //Printer is in a state where it can't react to manual control
            }
            return true;
        }

        MonitorSection
        {
            label: catalog.i18nc("@label", "Printer control")
            width: base.width
        }

        Row
        {
            width: base.width - 2 * UM.Theme.getSize("default_margin").width
            height: childrenRect.height + UM.Theme.getSize("default_margin").width
            anchors.left: parent.left
            anchors.leftMargin: UM.Theme.getSize("default_margin").width

            spacing: UM.Theme.getSize("default_margin").width

            Label
            {
                text: catalog.i18nc("@label", "Jog Position")
                color: UM.Theme.getColor("setting_control_text")
                font: UM.Theme.getFont("default")

                width: Math.floor(parent.width * 0.4) - UM.Theme.getSize("default_margin").width
                height: UM.Theme.getSize("setting_control").height
                verticalAlignment: Text.AlignVCenter
            }

            GridLayout
            {
                columns: 3
                rows: 4
                rowSpacing: UM.Theme.getSize("default_lining").width
                columnSpacing: UM.Theme.getSize("default_lining").height

                Label
                {
                    text: catalog.i18nc("@label", "X/Y")
                    color: UM.Theme.getColor("setting_control_text")
                    font: UM.Theme.getFont("default")
                    width: height
                    height: UM.Theme.getSize("setting_control").height
                    verticalAlignment: Text.AlignVCenter
                    horizontalAlignment: Text.AlignHCenter

                    Layout.row: 1
                    Layout.column: 2
                    Layout.preferredWidth: width
                    Layout.preferredHeight: height
                }

                Button
                {
                    Layout.row: 2
                    Layout.column: 2
                    Layout.preferredWidth: width
                    Layout.preferredHeight: height
                    iconSource: UM.Theme.getIcon("arrow_top");
                    style: monitorButtonStyle
                    width: height
                    height: UM.Theme.getSize("setting_control").height

                    onClicked:
                    {
                        printerModel.moveHead(0, distancesRow.currentDistance, 0)
                    }
                }

                Button
                {
                    Layout.row: 3
                    Layout.column: 1
                    Layout.preferredWidth: width
                    Layout.preferredHeight: height
                    iconSource: UM.Theme.getIcon("arrow_left");
                    style: monitorButtonStyle
                    width: height
                    height: UM.Theme.getSize("setting_control").height

                    onClicked:
                    {
                        printerModel.moveHead(-distancesRow.currentDistance, 0, 0)
                    }
                }

                Button
                {
                    Layout.row: 3
                    Layout.column: 3
                    Layout.preferredWidth: width
                    Layout.preferredHeight: height
                    iconSource: UM.Theme.getIcon("arrow_right");
                    style: monitorButtonStyle
                    width: height
                    height: UM.Theme.getSize("setting_control").height

                    onClicked:
                    {
                        printerModel.moveHead(distancesRow.currentDistance, 0, 0)
                    }
                }

                Button
                {
                    Layout.row: 4
                    Layout.column: 2
                    Layout.preferredWidth: width
                    Layout.preferredHeight: height
                    iconSource: UM.Theme.getIcon("arrow_bottom");
                    style: monitorButtonStyle
                    width: height
                    height: UM.Theme.getSize("setting_control").height

                    onClicked:
                    {
                        printerModel.moveHead(0, -distancesRow.currentDistance, 0)
                    }
                }

                Button
                {
                    Layout.row: 3
                    Layout.column: 2
                    Layout.preferredWidth: width
                    Layout.preferredHeight: height
                    iconSource: UM.Theme.getIcon("home");
                    style: monitorButtonStyle
                    width: height
                    height: UM.Theme.getSize("setting_control").height

                    onClicked:
                    {
                        printerModel.homeHead()
                    }
                }
            }


            Column
            {
                spacing: UM.Theme.getSize("default_lining").height

                Label
                {
                    text: catalog.i18nc("@label", "Z")
                    color: UM.Theme.getColor("setting_control_text")
                    font: UM.Theme.getFont("default")
                    width: UM.Theme.getSize("section").height
                    height: UM.Theme.getSize("setting_control").height
                    verticalAlignment: Text.AlignVCenter
                    horizontalAlignment: Text.AlignHCenter
                }

                Button
                {
                    iconSource: UM.Theme.getIcon("arrow_top");
                    style: monitorButtonStyle
                    width: height
                    height: UM.Theme.getSize("setting_control").height

                    onClicked:
                    {
                        printerModel.moveHead(0, 0, distancesRow.currentDistance)
                    }
                }

                Button
                {
                    iconSource: UM.Theme.getIcon("home");
                    style: monitorButtonStyle
                    width: height
                    height: UM.Theme.getSize("setting_control").height

                    onClicked:
                    {
                        printerModel.homeBed()
                    }
                }

                Button
                {
                    iconSource: UM.Theme.getIcon("arrow_bottom");
                    style: monitorButtonStyle
                    width: height
                    height: UM.Theme.getSize("setting_control").height

                    onClicked:
                    {
                        printerModel.moveHead(0, 0, -distancesRow.currentDistance)
                    }
                }
            }
        }

        Row
        {
            id: distancesRow

            width: base.width - 2 * UM.Theme.getSize("default_margin").width
            height: childrenRect.height + UM.Theme.getSize("default_margin").width
            anchors.left: parent.left
            anchors.leftMargin: UM.Theme.getSize("default_margin").width

            spacing: UM.Theme.getSize("default_margin").width

            property real currentDistance: 10

            Label
            {
                text: catalog.i18nc("@label", "Jog Distance")
                color: UM.Theme.getColor("setting_control_text")
                font: UM.Theme.getFont("default")

                width: Math.floor(parent.width * 0.4) - UM.Theme.getSize("default_margin").width
                height: UM.Theme.getSize("setting_control").height
                verticalAlignment: Text.AlignVCenter
            }

            Row
            {
                Repeater
                {
                    model: distancesModel
                    delegate: Button
                    {
                        height: UM.Theme.getSize("setting_control").height
                        width: height + UM.Theme.getSize("default_margin").width

                        text: model.label
                        exclusiveGroup: distanceGroup
                        checkable: true
                        checked: distancesRow.currentDistance == model.value
                        onClicked: distancesRow.currentDistance = model.value

                        style: ButtonStyle {
                            background: Rectangle {
                                border.width: control.checked ? UM.Theme.getSize("default_lining").width * 2 : UM.Theme.getSize("default_lining").width
                                border.color:
                                {
                                    if(!control.enabled)
                                    {
                                        return UM.Theme.getColor("action_button_disabled_border");
                                    }
                                    else if (control.checked || control.pressed)
                                    {
                                        return UM.Theme.getColor("action_button_active_border");
                                    }
                                    else if(control.hovered)
                                    {
                                        return UM.Theme.getColor("action_button_hovered_border");
                                    }
                                    return UM.Theme.getColor("action_button_border");
                                }
                                color:
                                {
                                    if(!control.enabled)
                                    {
                                        return UM.Theme.getColor("action_button_disabled");
                                    }
                                    else if (control.checked || control.pressed)
                                    {
                                        return UM.Theme.getColor("action_button_active");
                                    }
                                    else if (control.hovered)
                                    {
                                        return UM.Theme.getColor("action_button_hovered");
                                    }
                                    return UM.Theme.getColor("action_button");
                                }
                                Behavior on color { ColorAnimation { duration: 50; } }
                                Label {
                                    anchors.left: parent.left
                                    anchors.right: parent.right
                                    anchors.verticalCenter: parent.verticalCenter
                                    anchors.leftMargin: UM.Theme.getSize("default_lining").width * 2
                                    anchors.rightMargin: UM.Theme.getSize("default_lining").width * 2
                                    color:
                                    {
                                        if(!control.enabled)
                                        {
                                            return UM.Theme.getColor("action_button_disabled_text");
                                        }
                                        else if (control.checked || control.pressed)
                                        {
                                            return UM.Theme.getColor("action_button_active_text");
                                        }
                                        else if (control.hovered)
                                        {
                                            return UM.Theme.getColor("action_button_hovered_text");
                                        }
                                        return UM.Theme.getColor("action_button_text");
                                    }
                                    font: UM.Theme.getFont("default")
                                    text: control.text
                                    horizontalAlignment: Text.AlignHCenter
                                    elide: Text.ElideMiddle
                                }
                            }
                            label: Item { }
                        }
                    }
                }
            }
        }

        Row
        {
            id: customCommandInputRow

            width: base.width - 2 * UM.Theme.getSize("default_margin").width
            height: childrenRect.height + UM.Theme.getSize("default_margin").width
            anchors.left: parent.left
            anchors.leftMargin: UM.Theme.getSize("default_margin").width

            spacing: UM.Theme.getSize("default_margin").width

            Label
            {
                text: catalog.i18nc("@label", "Send G-code")
                color: UM.Theme.getColor("setting_control_text")
                font: UM.Theme.getFont("default")

                width: Math.floor(parent.width * 0.4) - UM.Theme.getSize("default_margin").width
                height: UM.Theme.getSize("setting_control").height
                verticalAlignment: Text.AlignVCenter
            }

            Row
            {
                // Input field for custom G-code commands.
                Rectangle
                {
                    id: customCommandControl

                    // state
                    visible: printerModel != null ? printerModel.canSendRawGcode: true
                    enabled: {
                        if (printerModel == null) {
                            return false // Can't send custom commands if not connected.
                        }
                        if (!connectedPrinter.acceptsCommands) {
                            return false // Not allowed to do anything
                        }
                        if (connectedPrinter.jobState == "printing" || connectedPrinter.jobState == "pre_print" || connectedPrinter.jobState == "resuming" || connectedPrinter.jobState == "pausing" || connectedPrinter.jobState == "paused" || connectedPrinter.jobState == "error" || connectedPrinter.jobState == "offline") {
                            return false // Printer is in a state where it can't react to custom commands.
                        }
                        return true
                    }

                    // style
                    color: !enabled ? UM.Theme.getColor("setting_control_disabled") : UM.Theme.getColor("setting_validation_ok")
                    border.width: UM.Theme.getSize("default_lining").width
                    border.color: !enabled ? UM.Theme.getColor("setting_control_disabled_border") : customCommandControlMouseArea.containsMouse ? UM.Theme.getColor("setting_control_border_highlight") : UM.Theme.getColor("setting_control_border")

                    // size
                    width: UM.Theme.getSize("setting_control").width
                    height: UM.Theme.getSize("setting_control").height

                    // highlight
                    Rectangle
                    {
                        anchors.fill: parent
                        anchors.margins: UM.Theme.getSize("default_lining").width
                        color: UM.Theme.getColor("setting_control_highlight")
                        opacity: customCommandControl.hovered ? 1.0 : 0
                    }

                    // cursor hover popup
                    MouseArea
                    {
                        id: customCommandControlMouseArea
                        hoverEnabled: true
                        anchors.fill: parent
                        cursorShape: Qt.IBeamCursor

                        onHoveredChanged:
                        {
                            if (containsMouse) {
                                base.showTooltip(
                                    base,
                                    { x: 0, y: customCommandControlMouseArea.mapToItem(base, 0, 0).y },
                                    catalog.i18nc("@tooltip of G-code command input", "Send a custom G-code command to the connected printer. Press 'enter' to send the command.")
                                )
                            } else {
                                base.hideTooltip()
                            }
                        }
                    }

                    TextInput
                    {
                        id: customCommandControlInput

                        // style
                        font: UM.Theme.getFont("default")
                        color: !enabled ? UM.Theme.getColor("setting_control_disabled_text") : UM.Theme.getColor("setting_control_text")
                        selectByMouse: true
                        clip: true
                        enabled: parent.enabled
                        renderType: Text.NativeRendering

                        // anchors
                        anchors.left: parent.left
                        anchors.leftMargin: UM.Theme.getSize("setting_unit_margin").width
                        anchors.right: parent.right
                        anchors.verticalCenter: parent.verticalCenter

                        // send the command when pressing enter
                        // we also clear the text field
                        Keys.onReturnPressed:
                        {
                            printerModel.sendRawCommand(customCommandControlInput.text)
                            customCommandControlInput.text = ""
                        }
                    }
                }
            }
        }

        ListModel
        {
            id: distancesModel
            ListElement { label: "0.1"; value: 0.1 }
            ListElement { label: "1";   value: 1   }
            ListElement { label: "10";  value: 10  }
            ListElement { label: "100"; value: 100 }
        }
        ExclusiveGroup { id: distanceGroup }
    }
}