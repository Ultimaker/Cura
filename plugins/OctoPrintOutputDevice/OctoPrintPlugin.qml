// Copyright (c) 2015 Ultimaker B.V.
// Uranium is released under the terms of the AGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1
import QtQuick.Layouts 1.1
import QtQuick.Dialogs 1.2
import QtQuick.Window 2.1

import UM 1.2 as UM
import Cura 1.0 as Cura

UM.Dialog
{
    id: dialog;


    title: catalog.i18nc("@title:window", "OctoPrint Servers");
    width: 800 * Screen.devicePixelRatio;
    height: 400 * Screen.devicePixelRatio;
    minimumWidth: 300 * Screen.devicePixelRatio;
    minimumHeight: 150 * Screen.devicePixelRatio;

    property string currentName: (instanceList.currentIndex != -1 ? instanceList.currentItem.name : "");
    property int defaultVerticalMargin: UM.Theme.getSize("default_margin").height;
    property int defaultHorizontalMargin: UM.Theme.getSize("default_margin").width;

    Row {
        id: buttons;

        width: childrenRect.width;
        height: childrenRect.height;

        Button {
            id: addButton;
            text: catalog.i18nc("@action:button", "Add");
            iconName: "list-add";
            onClicked: {
                instanceDialog.oldName = "";
                instanceDialog.name = "OctoPrint";
                instanceDialog.url = "http://octopi.local";
                instanceDialog.apiKey = "";
                instanceDialog.open();
                nameField.textChanged();
            }
        }
        Button {
            id: removeButton;
            text: catalog.i18nc("@action:button", "Remove");
            iconName: "list-remove";
            enabled: (instanceList.currentIndex != -1);
            onClicked: {
                var name = dialog.currentName;
                instanceList.currentIndex = -1;
                manager.removeInstance(name);
            }
        }
        Button {
            id: editButton;
            text: catalog.i18nc("@action:button", "Edit");
            iconName: "edit-rename";
            enabled: (instanceList.currentIndex != -1);
            onClicked: {
                instanceDialog.oldName = dialog.currentName;
                instanceDialog.name = dialog.currentName;
                instanceDialog.url = manager.instanceUrl(dialog.currentName);
                instanceDialog.apiKey = manager.instanceApiKey(dialog.currentName);
                instanceDialog.open();
                nameField.textChanged();
            }
        }
    }

    Item {
        UM.I18nCatalog { id: catalog; name: "cura"; }
        SystemPalette { id: palette }

        anchors {
            top: buttons.bottom;
            topMargin: parent.defaultVerticalMargin;
            left: parent.left;
            right: parent.right;
            bottom: parent.bottom;
        }

        ScrollView {
            id: instanceScroll;

            anchors {
                top: parent.top;
                topMargin: dialog.defaultVerticalMargin;
                bottom: parent.bottom;
                left: parent.left;
            }
            width: parent.width * 0.4;

            ListView {
                id: instanceList;

                anchors {
                    top: parent.top;
                    left: parent.left;
                }

                model: manager.serverList;

                delegate: Rectangle {
                    width: parent.width;
                    height: childrenRect.height;
                    color: ListView.isCurrentItem ? palette.highlight : index % 2 ? palette.base : palette.alternateBase;
                    property string name: modelData.toString();

                    Text {
                        text: name;
                    }

                    MouseArea {
                        anchors.fill: parent;
                        onClicked: {
                            if(!parent.ListView.isCurrentItem) {
                                parent.ListView.view.currentIndex = index;
                            }
                        }
                    }
                }
            }
        }

        Item {
            id: detailsPane;

            anchors {
                left: instanceScroll.right;
                leftMargin: dialog.defaultHorizontalMargin;
                top: parent.top;
                bottom: parent.bottom;
                right: parent.right;
            }

            ColumnLayout {
                anchors.margins: dialog.defaultVerticalMargin;

                Label {
                    text: dialog.currentName;
                    font: UM.Theme.getFont("large")
                    width: parent.width
                    elide: Text.ElideRight
                }

                Label { text: catalog.i18nc("@label", "Server Address (url)"); }
                Text { font.bold: true; text: manager.instanceUrl(dialog.currentName); }

                Label { text: catalog.i18nc("@label", "API Key"); }
                Text { font.bold: true; text: manager.instanceApiKey(dialog.currentName); }
            }

            visible: (instanceList.currentIndex != -1);
        }
    }

    Item {
        UM.Dialog {
            id: instanceDialog;

            property string oldName: ""; // oldName = "" for add
            property alias name: nameField.text;
            property alias url: urlField.text;
            property alias apiKey: apiKeyField.text;

            property bool validName: true;
            property real inputWidth: UM.Theme.getSize("standard_list_input").width * 1.5;

            width: 480 * Screen.devicePixelRatio;
            height: 240 * Screen.devicePixelRatio;

            onAccepted: {
                manager.saveInstance(oldName, nameField.text, urlField.text, apiKeyField.text);
                var index = instanceList.currentIndex;
                instanceList.currentIndex = -1;
                instanceList.currentIndexChanged();
                instanceList.currentIndex = index;
                instanceList.currentIndexChanged();
            }

            title: (oldName == "") ? catalog.i18nc("@window:title", "Add OctoPrint Server Connection") : catalog.i18nc("@window:title", "Edit OctoPrint Server Connection");

            Column {
                anchors.fill: parent;

                Label {
                    id: displayNameLabel;
                    text: catalog.i18nc("@label", "Display Name"); 
                }
                TextField {
                    id: nameField;
                    text: "";
                    implicitWidth: instanceDialog.inputWidth;
                    maximumLength: 40;
                    onTextChanged: {
                        instanceDialog.validName = manager.validName(instanceDialog.oldName, nameField.text);
                    }
                }

                Item { width: parent.width; height: displayNameLabel.height; }
                Label { text: catalog.i18nc("@label", "Server Address (url)"); }
                TextField {
                    id: urlField;
                    text: "";
                    implicitWidth: instanceDialog.inputWidth;
                    maximumLength: 1024;
                }

                Item { width: parent.width; height: displayNameLabel.height; }
                Label { text: catalog.i18nc("@label", "API Key (from OctoPrint Settings)"); }
                TextField {
                    id: apiKeyField;
                    text: "";
                    implicitWidth: instanceDialog.inputWidth;
                    maximumLength: 128;
                }

                Item { width: parent.width; height: displayNameLabel.height; }
                Label {
                    visible: !instanceDialog.validName;
                    text: catalog.i18nc("@error", "That instance name already exists.");
                }
            }

            rightButtons: [
                Button {
                    text: catalog.i18nc("@action:button", "Cancel");
                    onClicked: instanceDialog.reject();
                },
                Button {
                    id: okButton;
                    text: catalog.i18nc("@action:button", "Ok");
                    onClicked: instanceDialog.accept();
                    enabled: instanceDialog.validName;
                    isDefault: true;
                }
            ]
        }
    }
}
