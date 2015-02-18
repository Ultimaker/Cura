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

        //: Print Settings panel title
        Label { text: qsTr("Print Settings"); width: parent.width; font.capitalization: Font.AllUppercase; font.pointSize: UM.Theme.smallTextSize; }

        Item {
            width: parent.width;
            height: 24;

            Row {
                anchors.fill: parent;
                spacing: UM.Theme.defaultMargin;

                //: Material selection combo box label
                Label { text: qsTr("Material"); horizontalAlignment: Text.AlignRight; width: base.width * 0.5; }
                ComboBox {
                    width: parent.width * 0.35;
                    model: ListModel {
                        ListElement { text: "PLA"; }
                        ListElement { text: "ABS"; }
                    }
                    style: ComboBoxStyle { }
                }
            }
        }

        Item {
            width: parent.width;
            height: 24;

            Row {
                anchors.fill: parent;
                spacing: UM.Theme.defaultMargin;
                //: Time display label
                Label { text: qsTr("Time"); width: base.width * 0.5; horizontalAlignment: Text.AlignRight; }
                Label { text: Qt.formatTime(new Date(timeSlider.value * 60000)); width: base.width * 0.35; horizontalAlignment: Text.AlignLeft; }
            }
        }

        Rectangle { color: "black"; height: 1; width: parent.width; }

        Item {
            id: speedSlider;

            width: parent.width;
            height: 60;

            Slider {
                id: timeSlider;
                anchors.left: parent.left;
                anchors.right: parent.right;
                height: 20;

                minimumValue: 60;
                maximumValue: 600;
                stepSize: 10;

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

            Column {
                anchors.left: parent.left;
                anchors.bottom: parent.bottom;

                Label { text: Qt.formatTime(new Date(timeSlider.minimumValue * 60000)); }
                //: Low quality display label
                Label { text: qsTr("Low Quality"); }
            }

            Column {
                anchors.right: parent.right;
                anchors.bottom: parent.bottom;

                Label { text: Qt.formatTime(new Date(timeSlider.maximumValue * 60000)); anchors.right: parent.right; }
                //: High quality display label
                Label { text: qsTr("High Quality"); }
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
