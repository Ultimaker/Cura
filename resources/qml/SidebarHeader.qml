// Copyright (c) 2015 Ultimaker B.V.
// Cura is released under the terms of the AGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1
import QtQuick.Layouts 1.1

import UM 1.0 as UM

Column {
    id: base;

    property variant modesModel;
    property alias currentModeIndex: modeMenu.currentIndex;
    property Action addMachineAction;
    property Action configureMachinesAction;

    spacing: UM.Theme.sizes.default_margin.height;

    RowLayout {
        anchors.horizontalCenter: parent.horizontalCenter;

        width: parent.width - UM.Theme.sizes.default_margin.width * 2;
        height: UM.Theme.sizes.line.height;

        Label {
            //: Configuration mode label
            text: qsTr("Mode:");

            font: UM.Theme.fonts.sidebar_header;
            color: UM.Theme.colors.text_inactive;
        }

        ToolButton {
            text: base.modesModel ? base.modesModel.get(modeMenu.currentIndex).text : "";

            style: UM.Theme.styles.sidebar_header_button;

            Layout.preferredWidth: base.width * 0.25;

            menu: Menu {
                id: modeMenu;

                property int currentIndex: 0;

                Instantiator {
                    model: base.modesModel;

                    MenuItem {
                        text: model.text;
                        checkable: true;
                        checked: modeMenu.currentIndex == index;
                        exclusiveGroup: modeMenuGroup;
                        onTriggered: modeMenu.currentIndex = index;
                    }
                    onObjectAdded: modeMenu.insertItem(index, object)
                    onObjectRemoved: modeMenu.removeItem(object)
                }

                ExclusiveGroup { id: modeMenuGroup; }
            }
        }

        Rectangle {
            width: 1;
            height: parent.height;
            color: UM.Theme.colors.border;
        }

        Label {
            //: Machine selection label
            text: qsTr("Machine:");

            font: UM.Theme.fonts.sidebar_header;
            color: UM.Theme.colors.text_inactive;
        }

        ToolButton {
            id: machineButton;
            text: UM.Application.machineName;
            tooltip: UM.Application.machineName;

            style: UM.Theme.styles.sidebar_header_button;

            Layout.fillWidth: true;

            menu: Menu {
                id: machineMenu;
                Instantiator {
                    model: UM.Models.machinesModel
                    MenuItem {
                        text: model.name;
                        checkable: true;
                        checked: model.active;
                        exclusiveGroup: machineMenuGroup;
                        onTriggered: UM.Models.machinesModel.setActive(index)
                    }
                    onObjectAdded: machineMenu.insertItem(index, object)
                    onObjectRemoved: machineMenu.removeItem(object)
                }

                ExclusiveGroup { id: machineMenuGroup; }

                MenuSeparator { }

                MenuItem { action: base.addMachineAction; }
                MenuItem { action: base.configureMachinesAction; }
            }
        }
    }

    UM.SidebarCategoryHeader {
        width: parent.width;
        height: UM.Theme.sizes.section.height;

        iconSource: UM.Theme.icons.printsetup;

        //: Sidebar header label
        text: qsTr("Print Setup");
        enabled: false;

        color: UM.Theme.colors.primary;
    }
}
