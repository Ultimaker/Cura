// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.1

import UM 1.5 as UM

// This component creates a label with the abbreviated name of a printer, with a rectangle surrounding the label.
// It is created in a separated place in order to be reused whenever needed.
Item
{
    property alias text: printerTypeLabel.text

    property bool autoFit: false

    width: autoFit ? (printerTypeLabel.width + UM.Theme.getSize("default_margin").width) : UM.Theme.getSize("printer_type_label").width
    height: UM.Theme.getSize("printer_type_label").height

    Rectangle
    {
        anchors.fill: parent
        color: UM.Theme.getColor("printer_type_label_background")
        radius: UM.Theme.getSize("checkbox_radius").width
    }

    UM.Label
    {
        id: printerTypeLabel
        text: "CFFFP" // As an abbreviated name of the Custom FFF Printer
        anchors.verticalCenter: parent.verticalCenter
        anchors.horizontalCenter: parent.horizontalCenter
    }
}