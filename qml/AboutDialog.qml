import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Layouts 1.1
import QtQuick.Window 2.1

import UM 1.0 as UM

UM.Dialog {
    id: base

    //: Add Printer dialog title
    title: qsTr("About Cura");

    Label {
        text: "Cura";
    }

    rightButtons: Button {
        text: "Close";

        onClicked: base.visible = false;
    }
}

