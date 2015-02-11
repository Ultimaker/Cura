import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1
import QtQuick.Layouts 1.1

import UM 1.0 as UM

Rectangle {
    id: base;

    height: childrenRect.height;

    property real expandedHeight: 500;

    property bool collapsed: true;

    MouseArea {
        anchors.left: parent.left;
        anchors.right: parent.right;
        height: contents.height;

        acceptedButtons: Qt.AllButtons;

        onWheel: {
            wheel.accepted = true;
        }
    }

    Column {
        id: contents;
        spacing: UM.Theme.defaultMargin;

        anchors {
            left: parent.left;
            leftMargin: UM.Theme.defaultMargin;
            right: parent.right;
            rightMargin: UM.Theme.defaultMargin;
        }

        Label { text: "Print Settings"; width: parent.width; font.capitalization: Font.AllUppercase; font.pointSize: UM.Theme.smallTextSize; }

        Item {
            width: parent.width;
            height: childrenRect.height;

            Label { anchors.right: parent.horizontalCenter; text: "Material"; width: parent.width / 2; }
            ComboBox {
                anchors.left: parent.horizontalCenter;
                width: parent.width / 2;
                model: ListModel {
                    ListElement { text: "PLA"; }
                    ListElement { text: "ABS"; }
                }
            }
        }

        Item {
            width: parent.width;
            height: childrenRect.height;

            Label { anchors.right: parent.horizontalCenter; text: "Time"; width: parent.width / 2; }
            Label { anchors.left: parent.horizontalCenter; text: "10:10"; width: parent.width / 2; }
        }

        Rectangle { color: "black"; height: 1; width: parent.width; }

        Item {
            id: speedSlider;

            width: parent.width;
            height: 60;

            Slider {
                anchors.left: parent.left;
                anchors.right: parent.right;
                height: 20;

                style: SliderStyle {
                    groove: Rectangle {
                        height: 1;
                        color: "black";

                        Rectangle {
                            anchors.left: parent.left;
                            anchors.verticalCenter: parent.verticalCenter;
                            width: 1;
                            height: control.height;
                            color: "black";
                        }
                        Rectangle {
                            anchors.right: parent.right;
                            anchors.verticalCenter: parent.verticalCenter;
                            width: 1;
                            height: control.height;
                            color: "black";
                        }
                    }
                    handle: Rectangle { width: 5; height: control.height; color: UM.Theme.primaryColor; }
                }
            }

            Label {
                anchors.left: parent.left;
                anchors.bottom: parent.bottom;
                text: "0:00\nLow Quality";
            }

            Label {
                anchors.right: parent.right;
                anchors.bottom: parent.bottom;
                horizontalAlignment: Text.AlignRight;
                text: "10:00\nHigh Quality";
            }
        }

        UM.SettingsView { id: settingsView; width: parent.width; height: 0; opacity: 0; visible: false; verticalScrollBarPolicy: Qt.ScrollBarAlwaysOff }

        Rectangle { color: "black"; height: 1; width: parent.width; }

        Item {
            Layout.columnSpan: 2;
            height: childrenRect.height;
            width: parent.width;

            ToolButton {
                anchors.horizontalCenter: parent.horizontalCenter;
                iconSource: UM.Resources.getIcon('expand.png');
                onClicked: base.collapsed = !base.collapsed
            }
        }
    }

    states: [
        State {
            name: 'expanded';
            when: !base.collapsed;

            PropertyChanges { target: speedSlider; opacity: 0; height: 0; visible: false; }
            PropertyChanges {
                target: settingsView;
                opacity: 1;
                height: Math.min(settingsView.listHeight, base.expandedHeight * 0.6);
                visible: true;
                verticalScrollBarPolicy: Qt.ScrollBarAsNeeded;
            }
        }
    ]

    transitions: [
        Transition {
            to: 'expanded';
            reversible: true;
            SequentialAnimation {
                NumberAnimation { target: speedSlider; property: 'opacity'; duration: 100; }
                PropertyAction { target: settingsView; property: 'visible'; }
                NumberAnimation { property: 'height'; duration: 200; }
                PropertyAction { target: speedSlider; property: 'visible'; }
                NumberAnimation { target: settingsView; property: 'opacity'; duration: 100; }
            }
        }
    ]
}
