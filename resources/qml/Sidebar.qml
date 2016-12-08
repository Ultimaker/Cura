// Copyright (c) 2015 Ultimaker B.V.
// Cura is released under the terms of the AGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1
import QtQuick.Layouts 1.1

import UM 1.2 as UM
import Cura 1.0 as Cura
import "Menus"

Rectangle
{
    id: base;

    property int currentModeIndex;
    property bool monitoringPrint: false
    Connections
    {
        target: Printer
        onShowPrintMonitor:
        {
            base.monitoringPrint = show;
            showSettings.checked = !show;
            showMonitor.checked = show;
        }
    }

    // Is there an output device for this printer?
    property bool printerConnected: Cura.MachineManager.printerOutputDevices.length != 0
    property bool printerAcceptsCommands: printerConnected && Cura.MachineManager.printerOutputDevices[0].acceptsCommands

    color: UM.Theme.getColor("sidebar")
    UM.I18nCatalog { id: catalog; name:"cura"}

    Timer {
        id: tooltipDelayTimer
        interval: 500
        repeat: false
        property var item
        property string text

        onTriggered:
        {
            base.showTooltip(base, {x:1, y:item.y}, text);
        }
    }

    function showTooltip(item, position, text)
    {
        tooltip.text = text;
        position = item.mapToItem(base, position.x, position.y);
        tooltip.show(position);
    }

    function hideTooltip()
    {
        tooltip.hide();
    }

    function strPadLeft(string, pad, length) {
        return (new Array(length + 1).join(pad) + string).slice(-length);
    }

    function getPrettyTime(time)
    {
        var hours = Math.floor(time / 3600)
        time -= hours * 3600
        var minutes = Math.floor(time / 60);
        time -= minutes * 60
        var seconds = Math.floor(time);

        var finalTime = strPadLeft(hours, "0", 2) + ':' + strPadLeft(minutes,'0',2)+ ':' + strPadLeft(seconds,'0',2);
        return finalTime;
    }

    MouseArea
    {
        anchors.fill: parent
        acceptedButtons: Qt.AllButtons;

        onWheel:
        {
            wheel.accepted = true;
        }
    }

    // Printer selection and mode selection buttons for changing between Setting & Monitor print mode
    Rectangle
    {
        id: sidebarHeaderBar
        anchors.left: parent.left
        anchors.right: parent.right
        height: childrenRect.height
        color: UM.Theme.getColor("sidebar_header_bar")

        Row
        {
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.rightMargin: UM.Theme.getSize("default_margin").width
            spacing: UM.Theme.getSize("default_margin").width

            ToolButton
            {
                id: machineSelection
                text: Cura.MachineManager.activeMachineName

                width: parent.width - (showSettings.width + showMonitor.width + 2 * UM.Theme.getSize("default_margin").width)
                height: UM.Theme.getSize("sidebar_header").height
                tooltip: Cura.MachineManager.activeMachineName

                anchors.verticalCenter: parent.verticalCenter
                style: ButtonStyle {
                    background: Rectangle {
                        color: control.hovered ? UM.Theme.getColor("button_hover") :
                               control.pressed ? UM.Theme.getColor("button_hover") : UM.Theme.getColor("sidebar_header_bar")
                        Behavior on color { ColorAnimation { duration: 50; } }

                        UM.RecolorImage {
                            id: downArrow
                            anchors.verticalCenter: parent.verticalCenter
                            anchors.right: parent.right
                            anchors.rightMargin: UM.Theme.getSize("default_margin").width
                            width: UM.Theme.getSize("standard_arrow").width
                            height: UM.Theme.getSize("standard_arrow").height
                            sourceSize.width: width
                            sourceSize.height: width
                            color: UM.Theme.getColor("text_reversed")
                            source: UM.Theme.getIcon("arrow_bottom")
                        }
                        Label {
                            id: sidebarComboBoxLabel
                            color: UM.Theme.getColor("text_reversed")
                            text: control.text;
                            elide: Text.ElideRight;
                            anchors.left: parent.left;
                            anchors.leftMargin: UM.Theme.getSize("default_margin").width
                            anchors.right: downArrow.left;
                            anchors.rightMargin: control.rightMargin;
                            anchors.verticalCenter: parent.verticalCenter;
                            font: UM.Theme.getFont("large")
                        }
                    }
                    label: Label{}
                }

                menu: PrinterMenu { }
            }

            Button
            {
                id: showSettings
                width: height
                height: UM.Theme.getSize("sidebar_header").height
                onClicked: monitoringPrint = false
                iconSource: UM.Theme.getIcon("tab_settings");
                checkable: true
                checked: !monitoringPrint
                exclusiveGroup: sidebarHeaderBarGroup
                property string tooltipText: catalog.i18nc("@tooltip", "<b>Print Setup</b><br/><br/>Edit or review the settings for the active print job.")

                onHoveredChanged: {
                    if (hovered)
                    {
                        tooltipDelayTimer.item = showSettings
                        tooltipDelayTimer.text = tooltipText
                        tooltipDelayTimer.start();
                    }
                    else
                    {
                        tooltipDelayTimer.stop();
                        base.hideTooltip();
                    }
                }

                style:  UM.Theme.styles.sidebar_header_tab
            }

            Button
            {
                id: showMonitor
                width: height
                height: UM.Theme.getSize("sidebar_header").height
                onClicked: monitoringPrint = true
                iconSource: {
                    if(!printerConnected)
                        return UM.Theme.getIcon("tab_monitor");
                    else if(!printerAcceptsCommands)
                        return UM.Theme.getIcon("tab_monitor_unknown");

                    if(Cura.MachineManager.printerOutputDevices[0].printerState == "maintenance")
                    {
                        return UM.Theme.getIcon("tab_monitor_busy");
                    }

                    switch(Cura.MachineManager.printerOutputDevices[0].jobState)
                    {
                        case "printing":
                        case "pre_print":
                        case "wait_cleanup":
                            return UM.Theme.getIcon("tab_monitor_busy");
                        case "ready":
                        case "":
                            return UM.Theme.getIcon("tab_monitor_connected")
                        case "paused":
                            return UM.Theme.getIcon("tab_monitor_paused")
                        case "error":
                            return UM.Theme.getIcon("tab_monitor_stopped")
                        case "offline":
                            return UM.Theme.getIcon("tab_monitor_offline")
                        default:
                            return UM.Theme.getIcon("tab_monitor")
                    }
                }
                checkable: true
                checked: monitoringPrint
                exclusiveGroup: sidebarHeaderBarGroup
                property string tooltipText: catalog.i18nc("@tooltip", "<b>Print Monitor</b><br/><br/>Monitor the state of the connected printer and the print job in progress.")

                onHoveredChanged: {
                    if (hovered)
                    {
                        tooltipDelayTimer.item = showMonitor
                        tooltipDelayTimer.text = tooltipText
                        tooltipDelayTimer.start();
                    }
                    else
                    {
                        tooltipDelayTimer.stop();
                        base.hideTooltip();
                    }
                }

                style:  UM.Theme.styles.sidebar_header_tab
            }
            ExclusiveGroup { id: sidebarHeaderBarGroup }
        }
    }

    SidebarHeader {
        id: header
        width: parent.width

        anchors.top: sidebarHeaderBar.bottom

        onShowTooltip: base.showTooltip(item, location, text)
        onHideTooltip: base.hideTooltip()
    }

    Rectangle {
        id: headerSeparator
        width: parent.width
        visible: !monitoringPrint
        height: visible ? UM.Theme.getSize("sidebar_lining").height : 0
        color: UM.Theme.getColor("sidebar_lining")
        anchors.top: header.bottom
        anchors.topMargin: visible ? UM.Theme.getSize("default_margin").height : 0
    }

    onCurrentModeIndexChanged:
    {
        UM.Preferences.setValue("cura/active_mode", currentModeIndex);
        if(modesListModel.count > base.currentModeIndex)
        {
            sidebarContents.push({ "item": modesListModel.get(base.currentModeIndex).item, "replace": true });
        }
    }

    Label {
        id: settingsModeLabel
        text: catalog.i18nc("@label:listbox", "Print Setup");
        anchors.left: parent.left
        anchors.leftMargin: UM.Theme.getSize("default_margin").width;
        anchors.top: headerSeparator.bottom
        anchors.topMargin: UM.Theme.getSize("default_margin").height
        width: parent.width * 0.45 - 2 * UM.Theme.getSize("default_margin").width
        font: UM.Theme.getFont("large")
        color: UM.Theme.getColor("text")
        visible: !monitoringPrint
        elide: Text.ElideRight
    }

    Rectangle {
        id: settingsModeSelection
        width: parent.width * 0.55
        height: UM.Theme.getSize("sidebar_header_mode_toggle").height
        anchors.right: parent.right
        anchors.rightMargin: UM.Theme.getSize("default_margin").width
        anchors.top: headerSeparator.bottom
        anchors.topMargin: UM.Theme.getSize("default_margin").height
        visible: !monitoringPrint
        Component{
            id: wizardDelegate
            Button {
                height: settingsModeSelection.height
                anchors.left: parent.left
                anchors.leftMargin: model.index * (settingsModeSelection.width / 2)
                anchors.verticalCenter: parent.verticalCenter
                width: 0.5 * parent.width - (model.showFilterButton ? toggleFilterButton.width : 0)
                text: model.text
                exclusiveGroup: modeMenuGroup;
                checkable: true;
                checked: base.currentModeIndex == index
                onClicked: base.currentModeIndex = index

                onHoveredChanged: {
                    if (hovered)
                    {
                        tooltipDelayTimer.item = settingsModeSelection
                        tooltipDelayTimer.text = model.tooltipText
                        tooltipDelayTimer.start();
                    }
                    else
                    {
                        tooltipDelayTimer.stop();
                        base.hideTooltip();
                    }
                }

                style: ButtonStyle {
                    background: Rectangle {
                        border.width: UM.Theme.getSize("default_lining").width
                        border.color: control.checked ? UM.Theme.getColor("toggle_checked_border") :
                                          control.pressed ? UM.Theme.getColor("toggle_active_border") :
                                          control.hovered ? UM.Theme.getColor("toggle_hovered_border") : UM.Theme.getColor("toggle_unchecked_border")
                        color: control.checked ? UM.Theme.getColor("toggle_checked") :
                                   control.pressed ? UM.Theme.getColor("toggle_active") :
                                   control.hovered ? UM.Theme.getColor("toggle_hovered") : UM.Theme.getColor("toggle_unchecked")
                        Behavior on color { ColorAnimation { duration: 50; } }
                        Label {
                            anchors.centerIn: parent
                            color: control.checked ? UM.Theme.getColor("toggle_checked_text") :
                                       control.pressed ? UM.Theme.getColor("toggle_active_text") :
                                       control.hovered ? UM.Theme.getColor("toggle_hovered_text") : UM.Theme.getColor("toggle_unchecked_text")
                            font: UM.Theme.getFont("default")
                            text: control.text;
                        }
                    }
                    label: Item { }
                }
            }
        }
        ExclusiveGroup { id: modeMenuGroup; }
        ListView{
            id: modesList
            property var index: 0
            model: modesListModel
            delegate: wizardDelegate
            anchors.top: parent.top
            anchors.left: parent.left
            width: parent.width
        }
    }

    Button
    {
        id: toggleFilterButton

        anchors.right: parent.right
        anchors.rightMargin: UM.Theme.getSize("default_margin").width
        anchors.top: headerSeparator.bottom
        anchors.topMargin: UM.Theme.getSize("default_margin").height

        height: settingsModeSelection.height
        width: visible ? height : 0

        visible: !monitoringPrint && modesListModel.get(base.currentModeIndex) != undefined && modesListModel.get(base.currentModeIndex).showFilterButton
        opacity: visible ? 1 : 0

        onClicked: sidebarContents.currentItem.toggleFilterField()

        style: ButtonStyle
        {
            background: Rectangle
            {
                border.width: UM.Theme.getSize("default_lining").width
                border.color: UM.Theme.getColor("toggle_checked_border")
                color: visible ? UM.Theme.getColor("toggle_checked") : UM.Theme.getColor("toggle_hovered")
                Behavior on color { ColorAnimation { duration: 50; } }
            }
            label: UM.RecolorImage
            {
                anchors.verticalCenter: parent.verticalCenter
                anchors.right: parent.right
                anchors.rightMargin: UM.Theme.getSize("default_margin").width / 2

                source: UM.Theme.getIcon("search")
                color: UM.Theme.getColor("toggle_checked_text")
            }
        }
    }

    Label {
        id: monitorLabel
        text: catalog.i18nc("@label","Printer Monitor");
        anchors.left: parent.left
        anchors.leftMargin: UM.Theme.getSize("default_margin").width;
        anchors.top: headerSeparator.bottom
        anchors.topMargin: UM.Theme.getSize("default_margin").height
        width: parent.width * 0.45
        font: UM.Theme.getFont("large")
        color: UM.Theme.getColor("text")
        visible: monitoringPrint
    }

    StackView
    {
        id: sidebarContents

        anchors.bottom: footerSeparator.top
        anchors.top: settingsModeSelection.bottom
        anchors.topMargin: UM.Theme.getSize("default_margin").height
        anchors.left: base.left
        anchors.right: base.right
        visible: !monitoringPrint

        delegate: StackViewDelegate
        {
            function transitionFinished(properties)
            {
                properties.exitItem.opacity = 1
            }

            pushTransition: StackViewTransition
            {
                PropertyAnimation
                {
                    target: enterItem
                    property: "opacity"
                    from: 0
                    to: 1
                    duration: 100
                }
                PropertyAnimation
                {
                    target: exitItem
                    property: "opacity"
                    from: 1
                    to: 0
                    duration: 100
                }
            }
        }
    }

    Loader
    {
        anchors.bottom: footerSeparator.top
        anchors.top: monitorLabel.bottom
        anchors.topMargin: UM.Theme.getSize("default_margin").height
        anchors.left: base.left
        anchors.leftMargin: UM.Theme.getSize("default_margin").width
        anchors.right: base.right
        source: monitoringPrint ? "PrintMonitor.qml": "SidebarContents.qml"
   }

    Rectangle
    {
        id: footerSeparator
        width: parent.width
        height: UM.Theme.getSize("sidebar_lining").height
        color: UM.Theme.getColor("sidebar_lining")
        anchors.bottom: saveButton.top
        anchors.bottomMargin: UM.Theme.getSize("default_margin").height
    }

    SaveButton
    {
        id: saveButton
        implicitWidth: base.width
        implicitHeight: totalHeight
        anchors.bottom: parent.bottom
        visible: !monitoringPrint
    }

    MonitorButton
    {
        id: monitorButton
        implicitWidth: base.width
        implicitHeight: totalHeight
        anchors.bottom: parent.bottom
        visible: monitoringPrint
    }


    SidebarTooltip
    {
        id: tooltip;
    }

    ListModel
    {
        id: modesListModel;
    }

    SidebarSimple
    {
        id: sidebarSimple;
        visible: false;

        onShowTooltip: base.showTooltip(item, location, text)
        onHideTooltip: base.hideTooltip()
    }

    SidebarAdvanced
    {
        id: sidebarAdvanced;
        visible: false;

        onShowTooltip: base.showTooltip(item, location, text)
        onHideTooltip: base.hideTooltip()
    }

    Component.onCompleted:
    {
        modesListModel.append({
            text: catalog.i18nc("@title:tab", "Recommended"),
            tooltipText: catalog.i18nc("@tooltip", "<b>Recommended Print Setup</b><br/><br/>Print with the recommended settings for the selected printer, material and quality."),
            item: sidebarSimple,
            showFilterButton: false
        })
        modesListModel.append({
            text: catalog.i18nc("@title:tab", "Custom"),
            tooltipText: catalog.i18nc("@tooltip", "<b>Custom Print Setup</b><br/><br/>Print with finegrained control over every last bit of the slicing process."),
            item: sidebarAdvanced,
            showFilterButton: true
        })
        sidebarContents.push({ "item": modesListModel.get(base.currentModeIndex).item, "immediate": true });

        var index = parseInt(UM.Preferences.getValue("cura/active_mode"))
        if(index)
        {
            currentModeIndex = index;
        }
    }

    UM.SettingPropertyProvider
    {
        id: machineExtruderCount

        containerStackId: Cura.MachineManager.activeMachineId
        key: "machine_extruder_count"
        watchedProperties: [ "value" ]
        storeIndex: 0
    }

    UM.SettingPropertyProvider
    {
        id: machineHeatedBed

        containerStackId: Cura.MachineManager.activeMachineId
        key: "machine_heated_bed"
        watchedProperties: [ "value" ]
        storeIndex: 0
    }
}