import QtQuick 2.2
import QtQuick.Window 2.1
import QtQuick.Controls 1.1
import QtQuick.Layouts 1.1

import UM 1.0 as UM

Window {
    id: dialog

    title: qsTr("Cura Engine Log");

    modality: Qt.NonModal;
    flags: Qt.Dialog;

    width: 640;
    height: 480;

    Rectangle {
        anchors.fill: parent;
        color: UM.Theme.colors.system_window;

        ColumnLayout {
            anchors.fill: parent;
            anchors.margins: UM.Theme.sizes.default_margin.width;

            TextArea {
                id: textArea

                Layout.fillWidth: true
                Layout.fillHeight: true
            }

            Timer {
                id: updateTimer;
                interval: 1000;
                running: false;
                repeat: true;
                onTriggered: textArea.text = Printer.getEngineLog();
            }

            RowLayout {
                Item {
                    Layout.fillWidth: true;
                }
                Button {
                    text: qsTr("Close");
                    onClicked: dialog.visible = false;
                }
            }
        }
    }

    onVisibleChanged: {
        if(visible) {
            textArea.text = Printer.getEngineLog();
            updateTimer.start();
        } else {
            updateTimer.stop();
        }
    }
}
