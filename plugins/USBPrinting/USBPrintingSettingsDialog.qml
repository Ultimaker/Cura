// Copyright (c) 2026 UltiMaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.1

import UM 1.5 as UM
import Cura 1.1 as Cura

UM.Dialog
{
    id: dialog
    title: catalog.i18nc("@title:window", "USB Printing Settings")
    width: 460 * screenScaleFactor
    height: 320 * screenScaleFactor
    minimumWidth: 420 * screenScaleFactor
    minimumHeight: 280 * screenScaleFactor
    backgroundColor: UM.Theme.getColor("main_background")

    function portIndexFor(value) {        // First entry is always "Auto". The rest mirror manager.serialPorts.
        if (!value) {
            return 0;
        }
        var idx = manager.serialPorts.indexOf(value);
        return idx >= 0 ? idx + 1 : 0;
    }

    function baudIndexFor(value) {
        if (!value) {
            return 0;
        }
        var idx = manager.baudRateOptions.indexOf(value);
        return idx >= 0 ? idx : 0;
    }

    Item
    {
        id: base
        anchors.fill: parent

        UM.I18nCatalog { id: catalog; name: "cura" }

        ColumnLayout
        {
            anchors.fill: parent
            anchors.margins: UM.Theme.getSize("default_margin").width
            spacing: UM.Theme.getSize("default_margin").height

            UM.Label
            {
                text: catalog.i18nc("@label", "Pick a fixed COM port and baud rate to skip the slow baud-rate auto-detection. \"Auto\" keeps the current behaviour.")
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }

            GridLayout
            {
                columns: 3
                Layout.fillWidth: true
                columnSpacing: UM.Theme.getSize("narrow_margin").width
                rowSpacing: UM.Theme.getSize("narrow_margin").height

                UM.Label { text: catalog.i18nc("@label", "COM port:") }

                Cura.ComboBox
                {
                    id: portCombo
                    Layout.fillWidth: true
                    model: ["Auto"].concat(manager.serialPorts)
                    currentIndex: portIndexFor(manager.manualPort)
                    onActivated: manager.setManualPort(index == 0 ? "" : model[index])
                }

                Cura.SecondaryButton
                {
                    text: catalog.i18nc("@action:button", "Refresh")
                    onClicked: manager.refreshSerialPorts()
                }

                UM.Label { text: catalog.i18nc("@label", "Baud rate:") }

                Cura.ComboBox
                {
                    id: baudCombo
                    Layout.fillWidth: true
                    Layout.columnSpan: 2
                    model: manager.baudRateOptions
                    currentIndex: baudIndexFor(manager.manualBaudRate)
                    onActivated: manager.setManualBaudRate(index == 0 ? "" : model[index])
                }

                UM.Label
                {
                    text: catalog.i18nc("@label", "Diagnostics:")
                    Layout.columnSpan: 3
                }

                UM.CheckBox
                {
                    id: logCheckbox
                    Layout.columnSpan: 3
                    text: catalog.i18nc("@option:check", "Log USB communication to file")
                    checked: manager.logCommunication
                    onClicked: manager.setLogCommunication(checked)
                }

                UM.Label
                {
                    Layout.columnSpan: 3
                    Layout.fillWidth: true
                    wrapMode: Text.WordWrap
                    font.italic: true
                    text: manager.logFilePath
                }
            }

            UM.Label
            {
                text: catalog.i18nc("@label", "Changes are stored immediately. Press Reconnect to close the current USB connection and reconnect with the selected port/baud rate.")
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }

            Item { Layout.fillHeight: true }
        }
    }

    leftButtons: Cura.SecondaryButton
    {
        text: catalog.i18nc("@action:button", "Reconnect now")
        onClicked: manager.reconnect()
    }

    rightButtons: Cura.TertiaryButton
    {
        text: catalog.i18nc("@action:button", "Close")
        onClicked: dialog.accept()
    }
}
