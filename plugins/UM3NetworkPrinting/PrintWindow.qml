// Copyright (c) 2018 Ultimaker B.V.
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
    onVisibleChanged:
    {
        if(visible)
        {
            resetPrintersModel()
        }
        else
        {
            OutputDevice.cancelPrintSelection()
        }
    }
    title: catalog.i18nc("@title:window", "Print over network")

    property var printersModel:  ListModel{}
    function resetPrintersModel() {
        printersModel.clear()
        printersModel.append({ name: "Automatic", key: ""})

        for (var index in OutputDevice.printers)
        {
            printersModel.append({name: OutputDevice.printers[index].name, key: OutputDevice.printers[index].key})
        }
    }

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
            text: catalog.i18nc("@label", "Printer selection")
            wrapMode: Text.Wrap
            height: 20 * screenScaleFactor
        }

        ComboBox
        {
            id: printerSelectionCombobox
            model: base.printersModel
            textRole: "name"

            width: parent.width
            height: 40 * screenScaleFactor
            Behavior on height { NumberAnimation { duration: 100 } }
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
                printerSelectionCombobox.currentIndex = 0
                OutputDevice.cancelPrintSelection()
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
                OutputDevice.selectPrinter(printerSelectionCombobox.model.get(printerSelectionCombobox.currentIndex).key)
                // reset to defaults
                printerSelectionCombobox.currentIndex = 0
            }
        }
    ]
}
