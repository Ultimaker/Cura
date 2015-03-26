import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1
import QtQuick.Layouts 1.1

import UM 1.0 as UM

Column {
    id: base;

    property string currentModeFile: modeModel.get(modeMenu.currentIndex).file;
    property Action addMachineAction;
    property Action configureMachinesAction;

    spacing: UM.Theme.sizes.default_margin.height;

    RowLayout {
        anchors.horizontalCenter: parent.horizontalCenter;

        width: parent.width - UM.Theme.sizes.default_margin.width * 2;
        height: UM.Theme.sizes.line.height;

        Label {
            text: qsTr("Mode:");

            font: UM.Theme.fonts.sidebar_header;
            color: UM.Theme.colors.text_inactive;
        }

        ToolButton {
            text: qsTr(modeModel.get(modeMenu.currentIndex).text);

            style: UM.Theme.styles.sidebar_header_button;

            Layout.preferredWidth: base.width * 0.25;

            menu: Menu {
                id: modeMenu;

                property int currentIndex: 0;

                Instantiator {
                    model: ListModel {
                        id: modeModel;
                        ListElement { text: QT_TR_NOOP("Simple"); file: "SidebarSimple.qml" }
                        ListElement { text: QT_TR_NOOP("Advanced"); file: "SidebarAdvanced.qml" }
                    }

                    MenuItem {
                        text: qsTr(model.text);
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
            text: qsTr("Printer:");

            font: UM.Theme.fonts.sidebar_header;
            color: UM.Theme.colors.text_inactive;
        }

        ToolButton {
            id: machineButton;
            text: UM.Application.machineName;

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

    SidebarCategoryHeader {
        width: parent.width;
        height: UM.Theme.sizes.section.height;

        icon: UM.Theme.icons.printsetup;
        text: qsTr("Print Setup");
    }
}
