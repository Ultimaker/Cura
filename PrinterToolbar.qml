import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1
import QtQuick.Layouts 1.1

import UM 1.0 as UM

UM.Toolbar {
    id: base;

    property Action undo;
    property Action redo;
    property Action settings;

    Item { width: UM.Theme.windowLeftMargin; }

    Item {
        width: UM.Theme.panelWidth;
        Image { anchors.centerIn: parent; source: UM.Resources.getIcon("cura_logo.png"); }
    }

    Item { width: UM.Theme.toolbarSpacing; }

    ToolButton { style: UM.ToolbarButtonStyle { } action: base.undo; iconSource: UM.Resources.getIcon('undo.png'); }
    ToolButton { style: UM.ToolbarButtonStyle { } action: base.redo; iconSource: UM.Resources.getIcon('redo.png'); }

    //         Item { width: 10; }

    //         ToolButton { text: "3D"; onClicked: UM.Scene.setActiveCamera('3d'); }
    //         ToolButton { text: "Left"; onClicked: UM.Scene.setActiveCamera('left'); }
    //         ToolButton { text: "Top"; onClicked: UM.Scene.setActiveCamera('top'); }
    //         ToolButton { text: "Front"; onClicked: UM.Scene.setActiveCamera('front'); }

    Item { Layout.fillWidth: true; }

    Repeater {
        id: repeat

        model: UM.Models.toolModel

        ToolButton {
            style: UM.ToolbarButtonStyle { }

            text: model.name;
            iconSource: UM.Resources.getIcon(model.icon);
            tooltip: model.description;

            checkable: true;
            checked: model.active;

            //Workaround since using ToolButton's onClicked would break the binding of the checked property, instead
            //just catch the click so we do not trigger that behaviour.
            MouseArea {
                anchors.fill: parent;
                onClicked: parent.checked ? UM.Controller.setActiveTool(null) : UM.Controller.setActiveTool(model.id);
            }
        }
    }

    Item { Layout.fillWidth: true; }

    ToolButton {
        //: View Mode toolbar button
        text: qsTr("View Mode");
        iconSource: UM.Resources.getIcon("viewmode.png");

        style: UM.ToolbarButtonStyle { }

        menu: Menu {
            id: viewMenu;
            Instantiator {
                model: UM.Models.viewModel;
                MenuItem {
                    text: model.name;
                    checkable: true;
                    checked: model.active;
                    exclusiveGroup: viewMenuGroup;
                    onTriggered: UM.Controller.setActiveView(model.id);
                }
                onObjectAdded: viewMenu.insertItem(index, object)
                onObjectRemoved: viewMenu.removeItem(object)
            }

            ExclusiveGroup { id: viewMenuGroup; }
        }
    }

    Item { width: UM.Theme.toolbarSpacing; }

    ToolButton {
        id: machineButton;
        width: UM.Theme.panelWidth - UM.Theme.toolbarButtonWidth - 1;
        height: UM.Theme.toolbarButtonHeight;
        text: UM.Application.machineName;

        style: UM.ToolbarButtonStyle {
            backgroundColor: "white";
            backgroundHighlightColor: "#eee";

            label: Item {
                anchors.fill: parent;
                Label {
                    anchors {
                        top: parent.top;
                        topMargin: 2;
                        left: parent.left;
                        right: parent.right;
                    }
                    text: control.text;
                    elide: Text.ElideRight;
                    fontSizeMode: Text.HorizontalFit;
                    minimumPointSize: UM.Theme.smallTextSize;
                    font.pointSize: UM.Theme.largeTextSize;

                    verticalAlignment: Text.AlignBottom;
                }
                Label {
                    anchors.bottom: parent.bottom;
                    anchors.bottomMargin: 2;
                    anchors.left: parent.left;
                    //: Machine toolbar button
                    text: qsTr("Machine");
                    font.pointSize: UM.Theme.tinyTextSize;
                    font.capitalization: Font.AllUppercase;
                }
            }
        }

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
        }
    }

    ToolButton {
        style: UM.ToolbarButtonStyle {
            backgroundColor: "white";
            foregroundColor: "black";
            backgroundHighlightColor: "#eee";
            foregroundHighlightColor: "black";
        }
        action: base.settings;
    }

    Item { width: UM.Theme.windowRightMargin; }
}
