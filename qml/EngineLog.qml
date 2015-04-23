import QtQuick 2.2
import QtQuick.Window 2.1
import QtQuick.Controls 1.1
import QtQuick.Layouts 1.1

Window {
    id: dialog

    title: qsTr("Cura Engine Log");

    modality: Qt.NonModal;

    width: 640;

    TextArea {
        id: textArea

        anchors.left: parent.left;
        anchors.right: parent.right;

        implicitHeight: 480;
    }

    onVisibleChanged: {
        if(visible) {
            textArea.text = Printer.getEngineLog();
            updateTimer.start();
        } else {
            updateTimer.stop();
        }
    }

    Timer {
        id: updateTimer;
        interval: 1000;
        running: false;
        repeat: true;
        onTriggered: textArea.text = Printer.getEngineLog();
    }
}
