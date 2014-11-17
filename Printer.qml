import QtQuick 2.2
import QtQuick.Controls 1.2
import QtQuick.Layouts 1.1

import Cura 1.0 as Cura

Cura.MainWindow {
    id: base
    title: "Cura"
    visible: true

    backgroundColor: Qt.rgba(1.0, 0.0, 0.0, 1.0)
    application: curaApplication

    width: 1024
    height: 768

    Cura.FilePanel {
        anchors.left: parent.left
        anchors.verticalCenter: parent.verticalCenter
    }

    Cura.Panel {
        anchors.top: parent.top
        anchors.left: parent.left

        title: "Camera"

        contents: RowLayout {
            ToolButton { text: "3D" }
            ToolButton { text: "Left" }
            ToolButton { text: "Top" }
            ToolButton { text: "Front" }
        }
    }

    Cura.ToolPanel {
        anchors.top: parent.top;
        anchors.horizontalCenter: parent.horizontalCenter
    }

    Cura.Panel {
        anchors.top: parent.top
        anchors.right: parent.right

        title: "View"

        contents: ComboBox {
            model: ListModel {
                ListElement { text: "Normal" }
                ListElement { text: "Layers" }
            }
        }
    }

    Cura.Panel {
        anchors.right: parent.right;
        anchors.verticalCenter: parent.verticalCenter

        title: "Settings"

        contents: ColumnLayout {
            Layout.preferredWidth: 200
            Layout.preferredHeight: 400

            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true

                color: "grey"
            }

            Button {
                Layout.fillWidth: true
                text: "Save"
            }
        }
    }
}
