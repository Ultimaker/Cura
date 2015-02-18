import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Layouts 1.1

import UM 1.0 as UM

Rectangle {
    id: base;

    signal requestOpenFile();
    signal openFile(url file);

    function setDirectory(file)
    {
        UM.Models.directoryListModel.directory = file
    }

    MouseArea {
        anchors.fill: parent;
        acceptedButtons: Qt.AllButtons;

        onWheel: {
            wheel.accepted = true;
        }
    }

    ColumnLayout {
        anchors.fill: parent;
        anchors.margins: UM.Theme.defaultMargin;

        //: Open file button
        Button { text: qsTr("Open File"); iconSource: UM.Resources.getIcon("open.png"); Layout.fillWidth: true; onClicked: base.requestOpenFile(); }

        Rectangle {
            Layout.fillWidth: true;
            Layout.fillHeight: true;
            border.width: 1;
            border.color: "#aaa";

            ScrollView {
                anchors.fill: parent;
                anchors.margins: 1;

                ListView {
                    id: listView;
                    model: UM.Models.directoryListModel;
                    delegate: listDelegate;
                }
            }
        }

        ToolButton {
            anchors.horizontalCenter: parent.horizontalCenter;
            iconSource: UM.Resources.getIcon('expand.png');
        }
    }

    Component {
        id: listDelegate;
        Rectangle {
            id: item;

            anchors.left: parent.left;
            anchors.right: parent.right;

            height: 40;

            color: mouseArea.pressed ? "#f00" : index % 2 ? "#eee" : "#fff";

            Label {
                anchors.verticalCenter: parent.verticalCenter;
                anchors.left: parent.left;
                anchors.leftMargin: UM.Theme.defaultMargin;

                text: model.name;
            }

            MouseArea {
                id: mouseArea;
                anchors.fill: parent;

                onClicked: base.openFile(model.url);
            }
        }
    }
}
