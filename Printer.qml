import QtQuick 2.1
import QtQuick.Controls 1.1
import QtQuick.Layouts 1.1
import QtQuick.Dialogs 1.1

import UM 1.0 as UM

UM.DefaultWindow {
    title: "Cura"

    function saveClicked() {
        saveDialog.open();
    }

    FileDialog {
        id: saveDialog

        title: "Choose Filename"

        modality: Qt.NonModal;

        selectExisting: false;

        onAccepted:
        {
            Printer.saveGCode(fileUrl)
        }
    }
}
