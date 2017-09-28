// Copyright (c) 2015 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Window 2.2
import QtQuick.Controls 1.2

import UM 1.1 as UM

UM.Dialog
{
    id: base;

    minimumWidth: 500 * screenScaleFactor
    minimumHeight: 140 * screenScaleFactor
    maximumWidth: minimumWidth
    maximumHeight: minimumHeight
    width: minimumWidth
    height: minimumHeight

    visible: true
    modality: Qt.ApplicationModal

    title: catalog.i18nc("@title:window","Print over network")

    Column
    {
        id: printerSelection
        anchors.fill: parent
        anchors.top: parent.top
        anchors.topMargin: UM.Theme.getSize("default_margin").height
        anchors.leftMargin: UM.Theme.getSize("default_margin").width
        anchors.rightMargin: UM.Theme.getSize("default_margin").width
        height: 50 * screenScaleFactor

        Label
        {
            id: manualPrinterSelectionLabel
            anchors
            {
                left: parent.left
                topMargin: UM.Theme.getSize("default_margin").height
                right: parent.right
            }
            text: "Printer selection"
            wrapMode: Text.Wrap
            height: 20 * screenScaleFactor
        }

        ComboBox
        {
            id: printerSelectionCombobox
            model: OutputDevice.printers
            textRole: "friendly_name"

            width: parent.width
            height: 40 * screenScaleFactor
            Behavior on height { NumberAnimation { duration: 100 } }

            onActivated:
            {
                var printerData = OutputDevice.printers[index];
                OutputDevice.selectPrinter(printerData.unique_name, printerData.friendly_name);
            }
        }

        SystemPalette
        {
           id: palette
        }

        UM.I18nCatalog { id: catalog; name: "cura"; }
    }

    leftButtons: [
        Button
        {
            text: catalog.i18nc("@action:button","Cancel")
            enabled: true
            onClicked: {
                base.visible = false;
                // reset to defaults
                OutputDevice.selectAutomaticPrinter()
                printerSelectionCombobox.currentIndex = 0
            }
        }
    ]

    rightButtons: [
        Button
        {
            text: catalog.i18nc("@action:button","Print")
            enabled: true
            onClicked: {
                base.visible = false;
                OutputDevice.sendPrintJob();
                // reset to defaults
                OutputDevice.selectAutomaticPrinter()
                printerSelectionCombobox.currentIndex = 0
            }
        }
    ]
}
