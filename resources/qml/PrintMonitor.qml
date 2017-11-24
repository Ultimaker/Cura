// Copyright (c) 2017 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1
import QtQuick.Layouts 1.1

import UM 1.2 as UM
import Cura 1.0 as Cura

import "PrinterOutput"

Column
{
    id: printMonitor
    property var connectedDevice: Cura.MachineManager.printerOutputDevices.length >= 1 ? Cura.MachineManager.printerOutputDevices[0] : null
    property var activePrinter: connectedDevice != null ? connectedDevice.activePrinter : null
    property var activePrintJob: activePrinter != null ? activePrinter.activePrintJob: null

    Cura.ExtrudersModel
    {
        id: extrudersModel
        simpleNames: true
    }

    OutputDeviceHeader
    {
        width: parent.width
        outputDevice: connectedDevice
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
                model: activePrinter.extruders

                ExtruderBox
                {
                    color: UM.Theme.getColor("sidebar")
                    width: index == machineExtruderCount.properties.value - 1 && index % 2 == 0 ? extrudersGrid.width : Math.floor(extrudersGrid.width / 2 - UM.Theme.getSize("sidebar_lining_thin").width / 2)
                    extruderModel: modelData
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

    HeatedBedBox
    {
        visible: {
            if(activePrinter != null && activePrinter.bed_temperature != -1)
            {
                return true
            }
            return false
        }
        printerModel: activePrinter
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

    Column
    {
        visible: connectedPrinter != null ? connectedPrinter.canControlManually : false
        enabled:
        {
            if (connectedPrinter == null)
            {
                return false; //Can't control the printer if not connected.
            }
            if (!connectedPrinter.acceptsCommands)
            {
                return false; //Not allowed to do anything.
            }
            if (connectedPrinter.jobState == "printing" || connectedPrinter.jobState == "resuming" || connectedPrinter.jobState == "pausing" || connectedPrinter.jobState == "error" || connectedPrinter.jobState == "offline")
            {
                return false; //Printer is in a state where it can't react to manual control
            }
            return true;
        }

        Loader
        {
            sourceComponent: monitorSection
            property string label: catalog.i18nc("@label", "Printer control")
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
                        connectedPrinter.moveHead(0, distancesRow.currentDistance, 0)
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
                        connectedPrinter.moveHead(-distancesRow.currentDistance, 0, 0)
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
                        connectedPrinter.moveHead(distancesRow.currentDistance, 0, 0)
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
                        connectedPrinter.moveHead(0, -distancesRow.currentDistance, 0)
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
                        connectedPrinter.homeHead()
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
                        connectedPrinter.moveHead(0, 0, distancesRow.currentDistance)
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
                        connectedPrinter.homeBed()
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
                        connectedPrinter.moveHead(0, 0, -distancesRow.currentDistance)
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


    Loader
    {
        sourceComponent: monitorSection
        property string label: catalog.i18nc("@label", "Active print")
    }
    Loader
    {
        sourceComponent: monitorItem
        property string label: catalog.i18nc("@label", "Job Name")
        property string value: activePrintJob != null ? activePrintJob.name : ""
    }

    Loader
    {
        sourceComponent: monitorItem
        property string label: catalog.i18nc("@label", "Printing Time")
        property string value: activePrintJob != null ? getPrettyTime(activePrintJob.timeTotal) : ""
    }

    Loader
    {
        sourceComponent: monitorItem
        property string label: catalog.i18nc("@label", "Estimated time left")
        property string value: activePrintJob != null ? getPrettyTime(activePrintJob.timeTotal - activePrintJob.timeElapsed) : ""
        visible:
        {
            if(activePrintJob == null)
            {
                return false
            }

            return (activePrintJob.state == "printing" ||
                    activePrintJob.state == "resuming" ||
                    activePrintJob.state == "pausing" ||
                    activePrintJob.state == "paused")
        }
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
}