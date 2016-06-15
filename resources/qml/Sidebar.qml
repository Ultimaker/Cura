// Copyright (c) 2015 Ultimaker B.V.
// Cura is released under the terms of the AGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1
import QtQuick.Layouts 1.1

import UM 1.1 as UM
import Cura 1.0 as Cura

Rectangle
{
    id: base;

    property int currentModeIndex;
    property bool monitoringPrint: false

    // Is there an output device for this printer?
    property bool printerConnected: Cura.MachineManager.printerOutputDevices.length != 0

    color: UM.Theme.getColor("sidebar");
    UM.I18nCatalog { id: catalog; name:"cura"}

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

    MouseArea
    {
        anchors.fill: parent
        acceptedButtons: Qt.AllButtons;

        onWheel:
        {
            wheel.accepted = true;
        }
    }

    // Mode selection buttons for changing between Setting & Monitor print mode
    Row
    {
        id: settingAndMonitorButtons // Really need a better name for this.

        anchors.left: parent.left
        anchors.leftMargin: UM.Theme.getSize("default_margin").width;
        anchors.right: parent.right
        Button
        {
            width: (parent.width - UM.Theme.getSize("default_margin").width) / 2
            height: 50
            onClicked: monitoringPrint = false
            iconSource: UM.Theme.getIcon("tab_settings");
            style:  UM.Theme.styles.tool_button
            checkable: true
            checked: true
            exclusiveGroup: settingAndMonitorButtonsGroup
        }
        Button
        {
            width: (parent.width - UM.Theme.getSize("default_margin").width) / 2
            height: 50
            onClicked: monitoringPrint = true
            iconSource: UM.Theme.getIcon("tab_monitor");
            style:  UM.Theme.styles.tool_button
            checkable: true
            exclusiveGroup: settingAndMonitorButtonsGroup
        }
        ExclusiveGroup { id: settingAndMonitorButtonsGroup }
    }

    SidebarHeader {
        id: header
        width: parent.width
        height: totalHeightHeader

        anchors.top: settingAndMonitorButtons.bottom
        anchors.topMargin: UM.Theme.getSize("default_margin").height

        onShowTooltip: base.showTooltip(item, location, text)
        onHideTooltip: base.hideTooltip()
    }

    Rectangle {
        id: headerSeparator
        width: parent.width
        height: UM.Theme.getSize("sidebar_lining").height
        color: UM.Theme.getColor("sidebar_lining")
        anchors.top: header.bottom
        anchors.topMargin: UM.Theme.getSize("default_margin").height
    }

    currentModeIndex:
    {
        var index = parseInt(UM.Preferences.getValue("cura/active_mode"))
        if(index)
        {
            return index;
        }
        return 0;
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
        text: catalog.i18nc("@label:listbox","Setup");
        anchors.left: parent.left
        anchors.leftMargin: UM.Theme.getSize("default_margin").width;
        anchors.top: headerSeparator.bottom
        anchors.topMargin: UM.Theme.getSize("default_margin").height
        width: parent.width/100*45
        font: UM.Theme.getFont("large")
        color: UM.Theme.getColor("text")
        visible: !monitoringPrint
    }

    Rectangle {
        id: settingsModeSelection
        width: parent.width/100*55
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
                width: parent.width / 2
                text: model.text
                exclusiveGroup: modeMenuGroup;
                checkable: true;
                checked: base.currentModeIndex == index
                onClicked: base.currentModeIndex = index

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

    Label {
        id: monitorLabel
        text: catalog.i18nc("@label","Activity Data");
        anchors.left: parent.left
        anchors.leftMargin: UM.Theme.getSize("default_margin").width;
        anchors.top: headerSeparator.bottom
        anchors.topMargin: UM.Theme.getSize("default_margin").height
        width: parent.width/100*45
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

    // Item that holds all the print monitor properties
    Grid
    {
        id: printMonitor
        anchors.bottom: footerSeparator.top
        anchors.top: monitorLabel.bottom
        anchors.topMargin: UM.Theme.getSize("default_margin").height
        anchors.left: base.left
        anchors.leftMargin: UM.Theme.getSize("default_margin").width
        anchors.right: base.right
        visible: monitoringPrint
        columns: 2
        columnSpacing: UM.Theme.getSize("default_margin").width
        Label
        {
            text: "Temperature 1: "
        }
        Label
        {
            text: "" + Cura.MachineManager.printerOutputDevices[0].hotendTemperatures[0]
        }


        Label
        {
            text: "Temperature 2: "
        }
        Label
        {
            text: "" + Cura.MachineManager.printerOutputDevices[0].hotendTemperatures[1]
        }

    }

    Rectangle {
        id: footerSeparator
        width: parent.width
        height: UM.Theme.getSize("sidebar_lining").height
        color: UM.Theme.getColor("sidebar_lining")
        anchors.bottom: saveButton.top
        anchors.bottomMargin: UM.Theme.getSize("default_margin").height 
    }

    SaveButton
    {
        id: saveButton;
        implicitWidth: base.width
        implicitHeight: totalHeight
        anchors.bottom: parent.bottom
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
        modesListModel.append({ text: catalog.i18nc("@title:tab", "Simple"), item: sidebarSimple })
        modesListModel.append({ text: catalog.i18nc("@title:tab", "Advanced"), item: sidebarAdvanced })
        sidebarContents.push({ "item": modesListModel.get(base.currentModeIndex).item, "immediate": true });
    }
}
