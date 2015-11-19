// Copyright (c) 2015 Ultimaker B.V.
// Cura is released under the terms of the AGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1
import QtQuick.Layouts 1.1

import UM 1.1 as UM

Rectangle
{
    id: base;

    property Action addMachineAction;
    property Action configureMachinesAction;
    property Action manageProfilesAction;
    property int currentModeIndex;

    color: UM.Theme.colors.sidebar;
    UM.I18nCatalog { id: catalog; name:"cura"}

    function showTooltip(item, position, text)
    {
        tooltip.text = text;
        position = item.mapToItem(base, position.x, position.y / 2);
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

    SidebarHeader {
        id: header
        width: parent.width
        height: totalHeightHeader

        addMachineAction: base.addMachineAction;
        configureMachinesAction: base.configureMachinesAction;
    }

    Rectangle {
        id: headerSeparator
        width: parent.width
        height: UM.Theme.sizes.sidebar_lining.height
        color: UM.Theme.colors.sidebar_lining
        anchors.top: header.bottom
        anchors.topMargin: UM.Theme.sizes.default_margin.height 
    }

    ProfileSetup {
        id: profileItem
        manageProfilesAction: base.manageProfilesAction
        anchors.top: settingsModeSelection.bottom
        anchors.topMargin: UM.Theme.sizes.default_margin.height 
        width: parent.width
        height: totalHeightProfileSetup
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
    }

    Label {
        id: settingsModeLabel
        text: catalog.i18nc("@label:listbox","Setup");
        anchors.left: parent.left
        anchors.leftMargin: UM.Theme.sizes.default_margin.width;
        anchors.top: headerSeparator.bottom
        anchors.topMargin: UM.Theme.sizes.default_margin.height
        width: parent.width/100*45
        font: UM.Theme.fonts.large;
        color: UM.Theme.colors.text
    }

    Rectangle {
        id: settingsModeSelection
        width: parent.width/100*55
        height: UM.Theme.sizes.sidebar_header_mode_toggle.height
        anchors.right: parent.right
        anchors.rightMargin: UM.Theme.sizes.default_margin.width
        anchors.top: headerSeparator.bottom
        anchors.topMargin: UM.Theme.sizes.default_margin.height
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

                MouseArea {
                    anchors.fill: parent
                    cursorShape: checked ? Qt.ArrowCursor : Qt.PointingHandCursor
                    acceptedButtons: Qt.NoButton
                }

                style: ButtonStyle {
                    background: Rectangle {
                        border.color: control.checked ? UM.Theme.colors.toggle_checked_border : 
                                          control.pressed ? UM.Theme.colors.toggle_active_border :
                                          control.hovered ? UM.Theme.colors.toggle_hovered_border : UM.Theme.colors.toggle_unchecked_border
                        color: control.checked ? UM.Theme.colors.toggle_checked : 
                                   control.pressed ? UM.Theme.colors.toggle_active :
                                   control.hovered ? UM.Theme.colors.toggle_hovered : UM.Theme.colors.toggle_unchecked
                        Behavior on color { ColorAnimation { duration: 50; } }
                        Label {
                            anchors.centerIn: parent
                            color: control.checked ? UM.Theme.colors.toggle_checked_text : 
                                       control.pressed ? UM.Theme.colors.toggle_active_text :
                                       control.hovered ? UM.Theme.colors.toggle_hovered_text : UM.Theme.colors.toggle_unchecked_text
                            font: UM.Theme.fonts.default
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

    Loader
    {
        id: sidebarContents;
        anchors.bottom: footerSeparator.top
        anchors.top: profileItem.bottom
        anchors.topMargin: UM.Theme.sizes.default_margin.height
        anchors.left: base.left
        anchors.right: base.right

        source: modesListModel.count > base.currentModeIndex ? modesListModel.get(base.currentModeIndex).file : "";

        property Item sidebar: base;

        onLoaded:
        {
            if(item)
            {
                item.configureSettings = base.configureMachinesAction;
                if(item.onShowTooltip != undefined)
                {
                    item.showTooltip.connect(base.showTooltip)
                }
                if(item.onHideTooltip != undefined)
                {
                    item.hideTooltip.connect(base.hideTooltip)
                }
            }
        }
    }

    Rectangle {
        id: footerSeparator
        width: parent.width
        height: UM.Theme.sizes.sidebar_lining.height
        color: UM.Theme.colors.sidebar_lining
        anchors.bottom: saveButton.top
        anchors.bottomMargin: UM.Theme.sizes.default_margin.height 
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

    Component.onCompleted:
    {
        modesListModel.append({ text: catalog.i18nc("@title:tab", "Simple"), file: "SidebarSimple.qml" })
        modesListModel.append({ text: catalog.i18nc("@title:tab", "Advanced"), file: "SidebarAdvanced.qml" })
        sidebarContents.setSource(modesListModel.get(base.currentModeIndex).file)
    }
}
