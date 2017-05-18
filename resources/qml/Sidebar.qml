// Copyright (c) 2017 Ultimaker B.V.
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
    property bool monitoringPrint: false;  // When adding more "tabs", one want to replace this bool with a ListModel
    property bool hideSettings: PrintInformation.preSliced
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
    property int backendState: UM.Backend.state;

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
                        color: {
                            if(control.pressed) {
                                return UM.Theme.getColor("sidebar_header_active");
                            } else if(control.hovered) {
                                return UM.Theme.getColor("sidebar_header_hover");
                            } else {
                                return UM.Theme.getColor("sidebar_header_bar");
                            }
                        }
                        Behavior on color { ColorAnimation { duration: 50; } }

                        Rectangle {
                            id: underline;

                            anchors.left: parent.left
                            anchors.right: parent.right
                            anchors.bottom: parent.bottom
                            height: UM.Theme.getSize("sidebar_header_highlight").height
                            color: UM.Theme.getColor("sidebar_header_highlight_hover")
                            visible: control.hovered || control.pressed
                        }

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
                property color overlayColor: "transparent"
                property string overlayIconSource: ""

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
                iconSource: printerConnected ? UM.Theme.getIcon("tab_monitor_with_status") : UM.Theme.getIcon("tab_monitor")
                property color overlayColor:
                {
                    if(!printerAcceptsCommands)
                    {
                        return UM.Theme.getColor("status_unknown");
                    }

                    if(Cura.MachineManager.printerOutputDevices[0].printerState == "maintenance")
                    {
                        return UM.Theme.getColor("status_busy");
                    }
                    switch(Cura.MachineManager.printerOutputDevices[0].jobState)
                    {
                        case "printing":
                        case "pre_print":
                        case "wait_cleanup":
                        case "pausing":
                        case "resuming":
                            return UM.Theme.getColor("status_busy");
                        case "ready":
                        case "":
                            return UM.Theme.getColor("status_ready");
                        case "paused":
                            return UM.Theme.getColor("status_paused");
                        case "error":
                            return UM.Theme.getColor("status_stopped");
                        case "offline":
                            return UM.Theme.getColor("status_offline");
                        default:
                            return UM.Theme.getColor("text_reversed");
                    }
                }
                property string overlayIconSource:
                {
                    if(!printerConnected)
                    {
                        return "";
                    }
                    else if(!printerAcceptsCommands)
                    {
                        return UM.Theme.getIcon("tab_status_unknown");
                    }

                    if(Cura.MachineManager.printerOutputDevices[0].printerState == "maintenance")
                    {
                        return UM.Theme.getIcon("tab_status_busy");
                    }

                    switch(Cura.MachineManager.printerOutputDevices[0].jobState)
                    {
                        case "printing":
                        case "pre_print":
                        case "wait_cleanup":
                        case "pausing":
                        case "resuming":
                            return UM.Theme.getIcon("tab_status_busy");
                        case "ready":
                        case "":
                            return UM.Theme.getIcon("tab_status_connected")
                        case "paused":
                            return UM.Theme.getIcon("tab_status_paused")
                        case "error":
                            return UM.Theme.getIcon("tab_status_stopped")
                        case "offline":
                            return UM.Theme.getIcon("tab_status_offline")
                        default:
                            return ""
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
        visible: !monitoringPrint && !hideSettings
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

    Text {
        id: settingsModeLabel
        text: !hideSettings ? catalog.i18nc("@label:listbox", "Print Setup") : catalog.i18nc("@label:listbox","Print Setup disabled\nG-code files cannot be modified");
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
        color: "transparent"
        width: parent.width * 0.55
        height: UM.Theme.getSize("sidebar_header_mode_toggle").height
        anchors.right: parent.right
        anchors.rightMargin: UM.Theme.getSize("default_margin").width
        anchors.top: headerSeparator.bottom
        anchors.topMargin: UM.Theme.getSize("default_margin").height
        visible: !monitoringPrint && !hideSettings
        Component{
            id: wizardDelegate
            Button {
                height: settingsModeSelection.height
                anchors.left: parent.left
                anchors.leftMargin: model.index * (settingsModeSelection.width / 2)
                anchors.verticalCenter: parent.verticalCenter
                width: 0.5 * parent.width
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

        Label
        {
            id: toggleLeftText
            anchors.right: modeToggleSwitch.left
            anchors.rightMargin: UM.Theme.getSize("default_margin").width
            anchors.verticalCenter: parent.verticalCenter
            text: ""
            color:
            {
                if(toggleLeftTextMouseArea.containsMouse)
                {
                    return UM.Theme.getColor("mode_switch_text_hover");
                }
                else if(!modeToggleSwitch.checked)
                {
                    return UM.Theme.getColor("mode_switch_text_checked");
                }
                else
                {
                    return UM.Theme.getColor("mode_switch_text");
                }
            }
            font: UM.Theme.getFont("default")

            MouseArea
            {
                id: toggleLeftTextMouseArea
                hoverEnabled: true
                anchors.fill: parent
                onClicked:
                {
                    modeToggleSwitch.checked = false;
                }

                Component.onCompleted:
                {
                    clicked.connect(modeToggleSwitch.clicked)
                }
            }
        }

        Switch
        {
            id: modeToggleSwitch
            checked: false
            anchors.right: toggleRightText.left
            anchors.rightMargin: UM.Theme.getSize("default_margin").width
            anchors.verticalCenter: parent.verticalCenter

            property bool _hovered: modeToggleSwitchMouseArea.containsMouse || toggleLeftTextMouseArea.containsMouse || toggleRightTextMouseArea.containsMouse

            MouseArea
            {
                id: modeToggleSwitchMouseArea
                anchors.fill: parent
                hoverEnabled: true
                acceptedButtons: Qt.NoButton
            }

            onCheckedChanged:
            {
                var index = 0;
                if (checked)
                {
                    index = 1;
                }
                updateActiveMode(index);
            }

            function updateActiveMode(index)
            {
                base.currentModeIndex = index;
                UM.Preferences.setValue("cura/active_mode", index);
            }

            style: UM.Theme.styles.mode_switch
        }

        Label
        {
            id: toggleRightText
            anchors.right: parent.right
            anchors.verticalCenter: parent.verticalCenter
            text: ""
            color:
            {
                if(toggleRightTextMouseArea.containsMouse)
                {
                    return UM.Theme.getColor("mode_switch_text_hover");
                }
                else if(modeToggleSwitch.checked)
                {
                    return UM.Theme.getColor("mode_switch_text_checked");
                }
                else
                {
                    return UM.Theme.getColor("mode_switch_text");
                }
            }
            font: UM.Theme.getFont("default")

            MouseArea
            {
                id: toggleRightTextMouseArea
                hoverEnabled: true
                anchors.fill: parent
                onClicked:
                {
                    modeToggleSwitch.checked = true;
                }

                Component.onCompleted:
                {
                    clicked.connect(modeToggleSwitch.clicked)
                }
            }
        }
    }

    StackView
    {
        id: sidebarContents

        anchors.bottom: footerSeparator.top
        anchors.top: settingsModeSelection.bottom
        anchors.topMargin: UM.Theme.getSize("default_margin").height
        anchors.left: base.left
        anchors.right: base.right
        visible: !monitoringPrint && !hideSettings

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
        anchors.top: headerSeparator.bottom
        anchors.left: base.left
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

    // SaveButton and MonitorButton are actually the bottom footer panels.
    // "!monitoringPrint" currently means "show-settings-mode"
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

    // Setting mode: Recommended or Custom
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
            item: sidebarSimple
        })
        modesListModel.append({
            text: catalog.i18nc("@title:tab", "Custom"),
            tooltipText: catalog.i18nc("@tooltip", "<b>Custom Print Setup</b><br/><br/>Print with finegrained control over every last bit of the slicing process."),
            item: sidebarAdvanced
        })
        sidebarContents.push({ "item": modesListModel.get(base.currentModeIndex).item, "immediate": true });

        toggleLeftText.text = modesListModel.get(0).text;
        toggleRightText.text = modesListModel.get(1).text;

        var index = parseInt(UM.Preferences.getValue("cura/active_mode"));
        if (index)
        {
            currentModeIndex = index;
            modeToggleSwitch.checked = index > 0;
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
