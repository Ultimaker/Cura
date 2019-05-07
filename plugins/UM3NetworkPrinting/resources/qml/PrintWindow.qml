// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Window 2.2
import QtQuick.Controls 1.2
import UM 1.1 as UM

UM.Dialog {
    id: base;
    height: minimumHeight;
    leftButtons: [
        Button {
            enabled: true;
            onClicked: {
                base.visible = false;
                printerSelectionCombobox.currentIndex = 0;
                OutputDevice.cancelPrintSelection();
            }
            text: catalog.i18nc("@action:button","Cancel");
        }
    ]
    maximumHeight: minimumHeight;
    maximumWidth: minimumWidth;
    minimumHeight: 140 * screenScaleFactor;
    minimumWidth: 500 * screenScaleFactor;
    modality: Qt.ApplicationModal;
    onVisibleChanged: {
        if (visible) {
            resetPrintersModel();
        } else {
            OutputDevice.cancelPrintSelection();
        }
    }
    rightButtons: [
        Button {
            enabled: true;
            onClicked: {
                base.visible = false;
                OutputDevice.selectPrinter(printerSelectionCombobox.model.get(printerSelectionCombobox.currentIndex).key);
                // reset to defaults
                printerSelectionCombobox.currentIndex = 0;
            }
            text: catalog.i18nc("@action:button","Print");
        }
    ]
    title: catalog.i18nc("@title:window", "Print over network");
    visible: true;
    width: minimumWidth;

    Column {
        id: printerSelection;
        anchors {
            fill: parent;
            leftMargin: UM.Theme.getSize("default_margin").width;
            rightMargin: UM.Theme.getSize("default_margin").width;
            top: parent.top;
            topMargin: UM.Theme.getSize("default_margin").height;
        }
        height: 50 * screenScaleFactor;

        SystemPalette {
           id: palette;
        }

        UM.I18nCatalog {
            id: catalog;
            name: "cura";
        }

        Label {
            id: manualPrinterSelectionLabel;
            anchors {
                left: parent.left;
                right: parent.right;
                topMargin: UM.Theme.getSize("default_margin").height;
            }
            height: 20 * screenScaleFactor;
            text: catalog.i18nc("@label", "Printer selection");
            wrapMode: Text.Wrap;
            renderType: Text.NativeRendering;
        }

        ComboBox {
            id: printerSelectionCombobox;
            Behavior on height { NumberAnimation { duration: 100 } }
            height: 40 * screenScaleFactor;
            model: ListModel {
                id: printersModel;
            }
            textRole: "name";
            width: parent.width;
        }
    }

    // Utils
    function resetPrintersModel() {
        printersModel.clear();
        printersModel.append({ name: "Automatic", key: ""});
        for (var index in OutputDevice.printers) {
            printersModel.append({name: OutputDevice.printers[index].name, key: OutputDevice.printers[index].key});
        }
    }
}
