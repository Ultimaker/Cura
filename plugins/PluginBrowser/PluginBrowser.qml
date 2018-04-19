// Copyright (c) 2017 Ultimaker B.V.
// PluginBrowser is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Dialogs 1.1
import QtQuick.Window 2.2
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4

// TODO: Switch to QtQuick.Controls 2.x and remove QtQuick.Controls.Styles

import UM 1.1 as UM

Window {
    id: base

    title: catalog.i18nc("@title:tab", "Plugins");
    modality: Qt.ApplicationModal
    width: 800 * screenScaleFactor
    height: 640 * screenScaleFactor
    minimumWidth: 350 * screenScaleFactor
    minimumHeight: 350 * screenScaleFactor
    color: UM.Theme.getColor("sidebar")

    Item {
        id: view
        anchors {
            fill: parent
            leftMargin: UM.Theme.getSize("default_margin").width
            rightMargin: UM.Theme.getSize("default_margin").width
            topMargin: UM.Theme.getSize("default_margin").height
            bottomMargin: UM.Theme.getSize("default_margin").height
        }

        Rectangle {
            id: topBar
            width: parent.width
            color: "transparent"
            height: childrenRect.height

            Row {
                spacing: 12
                height: childrenRect.height
                width: childrenRect.width
                anchors.horizontalCenter: parent.horizontalCenter

                Button {
                    text: "Install"
                    style: ButtonStyle {
                        background: Rectangle {
                            color: "transparent"
                            implicitWidth: 96
                            implicitHeight: 48
                            Rectangle {
                                visible: manager.viewing == "available" ? true : false
                                color: UM.Theme.getColor("primary")
                                anchors.bottom: parent.bottom
                                width: parent.width
                                height: 3
                            }
                        }
                        label: Text {
                            text: control.text
                            color: UM.Theme.getColor("text")
                            font {
                                pixelSize: 15
                            }
                            verticalAlignment: Text.AlignVCenter
                            horizontalAlignment: Text.AlignHCenter
                        }
                    }
                    onClicked: manager.setView("available")
                }

                Button {
                    text: "Manage"
                    style: ButtonStyle {
                        background: Rectangle {
                            color: "transparent"
                            implicitWidth: 96
                            implicitHeight: 48
                            Rectangle {
                                visible: manager.viewing == "installed" ? true : false
                                color: UM.Theme.getColor("primary")
                                anchors.bottom: parent.bottom
                                width: parent.width
                                height: 3
                            }
                        }
                        label: Text {
                            text: control.text
                            color: UM.Theme.getColor("text")
                            font {
                                pixelSize: 15
                            }
                            verticalAlignment: Text.AlignVCenter
                            horizontalAlignment: Text.AlignHCenter
                        }
                    }
                    onClicked: manager.setView("installed")
                }
            }
        }

        // Scroll view breaks in QtQuick.Controls 2.x
        ScrollView {
            id: installedPluginList
            width: parent.width
            height: 400

            anchors {
                top: topBar.bottom
                topMargin: UM.Theme.getSize("default_margin").height
                bottom: bottomBar.top
                bottomMargin: UM.Theme.getSize("default_margin").height
            }

            frameVisible: true

            ListView {
                id: pluginList
                property var activePlugin
                property var filter: "installed"

                anchors.fill: parent

                model: manager.pluginsModel
                delegate: PluginEntry {}
            }
        }

        Rectangle {
            id: bottomBar
            width: parent.width
            height: childrenRect.height
            color: "transparent"
            anchors.bottom: parent.bottom

            Label {
                visible: manager.restartRequired
                text: "You will need to restart Cura before changes in plugins have effect."
                height: 30
                verticalAlignment: Text.AlignVCenter
            }
            Button {
                id: restartChangedButton
                text: "Quit Cura"
                anchors.right: closeButton.left
                anchors.rightMargin: UM.Theme.getSize("default_margin").width
                visible: manager.restartRequired
                iconName: "dialog-restart"
                onClicked: manager.restart()
                style: ButtonStyle {
                    background: Rectangle {
                        implicitWidth: 96
                        implicitHeight: 30
                        color: UM.Theme.getColor("primary")
                    }
                    label: Text {
                        verticalAlignment: Text.AlignVCenter
                        color: UM.Theme.getColor("button_text")
                        font {
                            pixelSize: 13
                            bold: true
                        }
                        text: control.text
                        horizontalAlignment: Text.AlignHCenter
                    }
                }
            }

            Button {
                id: closeButton
                text: catalog.i18nc("@action:button", "Close")
                iconName: "dialog-close"
                onClicked: {
                    if ( manager.isDownloading ) {
                        manager.cancelDownload()
                    }
                    base.close();
                }
                anchors.right: parent.right
                style: ButtonStyle {
                    background: Rectangle {
                        color: "transparent"
                        implicitWidth: 96
                        implicitHeight: 30
                        border {
                            width: 1
                            color: UM.Theme.getColor("lining")
                        }
                    }
                    label: Text {
                        verticalAlignment: Text.AlignVCenter
                        color: UM.Theme.getColor("text")
                        text: control.text
                        horizontalAlignment: Text.AlignHCenter
                    }
                }
            }
        }

        UM.I18nCatalog { id: catalog; name: "cura" }

        Connections {
            target: manager
            onShowLicenseDialog: {
                licenseDialog.pluginName = manager.getLicenseDialogPluginName();
                licenseDialog.licenseContent = manager.getLicenseDialogLicenseContent();
                licenseDialog.pluginFileLocation = manager.getLicenseDialogPluginFileLocation();
                licenseDialog.show();
            }
        }

        UM.Dialog {
            id: licenseDialog
            title: catalog.i18nc("@title:window", "Plugin License Agreement")

            minimumWidth: UM.Theme.getSize("license_window_minimum").width
            minimumHeight: UM.Theme.getSize("license_window_minimum").height
            width: minimumWidth
            height: minimumHeight

            property var pluginName;
            property var licenseContent;
            property var pluginFileLocation;

            Item
            {
                anchors.fill: parent

                Label
                {
                    id: licenseTitle
                    anchors.top: parent.top
                    anchors.left: parent.left
                    anchors.right: parent.right
                    text: licenseDialog.pluginName + catalog.i18nc("@label", "This plugin contains a license.\nYou need to accept this license to install this plugin.\nDo you agree with the terms below?")
                    wrapMode: Text.Wrap
                }

                TextArea
                {
                    id: licenseText
                    anchors.top: licenseTitle.bottom
                    anchors.bottom: parent.bottom
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.topMargin: UM.Theme.getSize("default_margin").height
                    readOnly: true
                    text: licenseDialog.licenseContent != null ? licenseDialog.licenseContent : ""
                }
            }

            rightButtons: [
                Button
                {
                    id: acceptButton
                    anchors.margins: UM.Theme.getSize("default_margin").width
                    text: catalog.i18nc("@action:button", "Accept")
                    onClicked:
                    {
                        licenseDialog.close();
                        manager.installPlugin(licenseDialog.pluginFileLocation);
                    }
                },
                Button
                {
                    id: declineButton
                    anchors.margins: UM.Theme.getSize("default_margin").width
                    text: catalog.i18nc("@action:button", "Decline")
                    onClicked:
                    {
                        licenseDialog.close();
                    }
                }
            ]
        }

        Connections {
            target: manager
            onShowRestartDialog: {
                restartDialog.message = manager.getRestartDialogMessage();
                restartDialog.show();
            }
        }

        Window {
            id: restartDialog
            // title: catalog.i18nc("@title:tab", "Plugins");
            width: 360 * screenScaleFactor
            height: 120 * screenScaleFactor
            minimumWidth: 360 * screenScaleFactor
            minimumHeight: 120 * screenScaleFactor
            color: UM.Theme.getColor("sidebar")
            property var message;

            Text {
                id: message
                anchors {
                    left: parent.left
                    leftMargin: UM.Theme.getSize("default_margin").width
                    top: parent.top
                    topMargin: UM.Theme.getSize("default_margin").height
                }
                text: restartDialog.message != null ? restartDialog.message : ""
            }
            Button {
                id: laterButton
                text: "Later"
                onClicked: restartDialog.close();
                anchors {
                    left: parent.left
                    leftMargin: UM.Theme.getSize("default_margin").width
                    bottom: parent.bottom
                    bottomMargin: UM.Theme.getSize("default_margin").height
                }
                style: ButtonStyle {
                    background: Rectangle {
                        color: "transparent"
                        implicitWidth: 96
                        implicitHeight: 30
                        border {
                            width: 1
                            color: UM.Theme.getColor("lining")
                        }
                    }
                    label: Text {
                        verticalAlignment: Text.AlignVCenter
                        color: UM.Theme.getColor("text")
                        text: control.text
                        horizontalAlignment: Text.AlignHCenter
                    }
                }
            }


            Button {
                id: restartButton
                text: "Quit Cura"
                anchors {
                    right: parent.right
                    rightMargin: UM.Theme.getSize("default_margin").width
                    bottom: parent.bottom
                    bottomMargin: UM.Theme.getSize("default_margin").height
                }
                onClicked: manager.restart()
                style: ButtonStyle {
                    background: Rectangle {
                        implicitWidth: 96
                        implicitHeight: 30
                        color: UM.Theme.getColor("primary")
                    }
                    label: Text {
                        verticalAlignment: Text.AlignVCenter
                        color: UM.Theme.getColor("button_text")
                        font {
                            pixelSize: 13
                            bold: true
                        }
                        text: control.text
                        horizontalAlignment: Text.AlignHCenter
                    }
                }
            }
        }

    }
}
