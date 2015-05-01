import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Layouts 1.1

import UM 1.0 as UM

UM.Dialog {
    id: dialog;

    //: Engine Log dialog title
    title: qsTr("Engine Log");

    modality: Qt.NonModal;

    TextArea {
        id: textArea
        anchors.fill: parent;

        Timer {
            id: updateTimer;
            interval: 1000;
            running: false;
            repeat: true;
            onTriggered: textArea.text = Printer.getEngineLog();
        }
    }

    rightButtons: Button {
        text: qsTr("Close");
        onClicked: dialog.visible = false;
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
