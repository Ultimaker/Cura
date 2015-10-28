// Copyright (c) 2015 Ultimaker B.V.
// Cura is released under the terms of the AGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1

import UM 1.1 as UM

Item
{
    id: base;
    // Machine Setup
    property variant modesModel;
    property int currentModeIndex: 0;
    property Action addMachineAction;
    property Action configureMachinesAction;
    UM.I18nCatalog { id: catalog; name:"cura"}
    property int totalHeightHeader: childrenRect.height

    Rectangle {
        id: settingsModeRow
        width: base.width
        height: UM.Theme.sizes.sidebar_header.height
        anchors.top: parent.top
        color: UM.Theme.colors.sidebar_header_bar

        Label{
            id: settingsModeLabel
            text: catalog.i18nc("@label:listbox","Print Setup");
            anchors.left: parent.left
            anchors.leftMargin: UM.Theme.sizes.default_margin.width;
            anchors.verticalCenter: parent.verticalCenter
            width: parent.width/100*45
            font: UM.Theme.fonts.default;
            color: UM.Theme.colors.text_white
        }

        Rectangle{
            id: settingsModeSelection
            width: parent.width/100*55
            height: UM.Theme.sizes.sidebar_header_mode_toggle.height
            anchors.right: parent.right
            anchors.rightMargin: UM.Theme.sizes.default_margin.width;
            anchors.verticalCenter: parent.verticalCenter
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
                            color: control.checked ? UM.Theme.colors.toggle_active : UM.Theme.colors.toggle_disabled
                            Behavior on color { ColorAnimation { duration: 50; } }
                            Label {
                                anchors.centerIn: parent
                                color: control.checked ? UM.Theme.colors.toggle_active_text : UM.Theme.colors.toggle_disabled_text
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
                model: base.modesModel
                delegate: wizardDelegate
                anchors.top: parent.top
                anchors.left: parent.left
                width: parent.width
            }
        }
    }

    Rectangle {
        id: machineSelectionRow
        width: base.width
        height: UM.Theme.sizes.sidebar_setup.height
        anchors.top: settingsModeRow.bottom
        anchors.topMargin: UM.Theme.sizes.default_margin.height
        anchors.horizontalCenter: parent.horizontalCenter

        Label{
            id: machineSelectionLabel
            //: Machine selection label
            text: catalog.i18nc("@label:listbox","Machine:");
            anchors.left: parent.left
            anchors.leftMargin: UM.Theme.sizes.default_margin.width
            anchors.verticalCenter: parent.verticalCenter
            font: UM.Theme.fonts.default;
        }

        ToolButton {
            id: machineSelection
            text: UM.MachineManager.activeMachineInstance;
            width: parent.width/100*55
            height: UM.Theme.sizes.setting_control.height
            tooltip: UM.MachineManager.activeMachineInstance;
            anchors.right: parent.right
            anchors.rightMargin: UM.Theme.sizes.default_margin.width
            anchors.verticalCenter: parent.verticalCenter
            style: UM.Theme.styles.sidebar_header_button

            menu: Menu
            {
                id: machineSelectionMenu
                Instantiator
                {
                    model: UM.MachineInstancesModel { }
                    MenuItem
                    {
                        text: model.name;
                        checkable: true;
                        checked: model.active;
                        exclusiveGroup: machineSelectionMenuGroup;
                        onTriggered: UM.MachineManager.setActiveMachineInstance(model.name);
                    }
                    onObjectAdded: machineSelectionMenu.insertItem(index, object)
                    onObjectRemoved: machineSelectionMenu.removeItem(object)
                }

                ExclusiveGroup { id: machineSelectionMenuGroup; }

                MenuSeparator { }

                MenuItem { action: base.addMachineAction; }
                MenuItem { action: base.configureMachinesAction; }
            }
        }
    }
}
