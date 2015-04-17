import QtQuick 2.2
import QtQuick.Dialogs 1.2
import QtQuick.Controls 1.2
import QtQuick.Layouts 1.1

Dialog {
    id: dialog

    title: qsTr("Cura Engine Log");

    standardButtons: StandardButton.Close;
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
