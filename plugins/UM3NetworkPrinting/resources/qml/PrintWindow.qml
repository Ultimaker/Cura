// Copyright (c) 2019 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.
import QtQuick 2.2
import QtQuick.Window 2.2
import QtQuick.Controls 1.2
import UM 1.1 as UM

UM.Dialog {

    id: base;
    title: catalog.i18nc("@title:window", "Print over network");
    width: minimumWidth;
    height: minimumHeight;
    maximumHeight: minimumHeight;
    maximumWidth: minimumWidth;
    minimumHeight: 140 * screenScaleFactor;
    minimumWidth: 500 * screenScaleFactor;
    modality: Qt.ApplicationModal;

    Component.onCompleted: {
        populateComboBox()
    }

    // populates the combo box with the correct printer values
    function populateComboBox() {
        comboBoxPrintersModel.clear();
        comboBoxPrintersModel.append({ name: "Automatic", key: "" });  // Connect will just do it's thing
        for (var i in OutputDevice.printers) {
            comboBoxPrintersModel.append({
                name: OutputDevice.printers[i].name,
                key: OutputDevice.printers[i].uniqueName
            });
        }
    }

    leftButtons: [
        Button {
            enabled: true;
            onClicked: {
                base.close();
            }
            text: catalog.i18nc("@action:button","Cancel");
        }
    ]
    rightButtons: [
        Button {
            enabled: true;
            onClicked: {
                OutputDevice.selectTargetPrinter(printerComboBox.model.get(printerComboBox.currentIndex).key);
                base.close();
            }
            text: catalog.i18nc("@action:button","Print");
        }
    ]

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
            id: printerComboBox;
            Behavior on height { NumberAnimation { duration: 100 } }
            height: 40 * screenScaleFactor;
            model: ListModel {
                id: comboBoxPrintersModel;
            }
            textRole: "name";
            width: parent.width;
        }
    }
}
