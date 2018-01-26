// Copyright (c) 2017 Ultimaker B.V.
// PluginBrowser is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Dialogs 1.1
import QtQuick.Window 2.2
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4

// TODO: Switch to QtQuick.Controls 2.x and remove QtQuick.Controls.Styles

import UM 1.1 as UM

Component {
    id: pluginDelegate

    Rectangle {

        // Don't show required plugins as they can't be managed anyway:
        height: !model.required ? 84 : 0
        visible: !model.required ? true : false
        color: "transparent"
        anchors {
            left: parent.left
            leftMargin: UM.Theme.getSize("default_margin").width
            right: parent.right
            rightMargin: UM.Theme.getSize("default_margin").width
        }


        // Bottom border:
        Rectangle {
            color: UM.Theme.getColor("lining")
            width: parent.width
            height: 1
            anchors.bottom: parent.bottom
        }

        // Plugin info
        Column {
            id: pluginInfo

            property var color: model.enabled ? UM.Theme.getColor("text") : UM.Theme.getColor("lining")

            // Styling:
            height: parent.height
            anchors {
                left: parent.left
                top: parent.top
                topMargin: UM.Theme.getSize("default_margin").height
                right: authorInfo.left
                rightMargin: UM.Theme.getSize("default_margin").width
            }


            Label {
                text: model.name
                width: parent.width
                height: 24
                wrapMode: Text.WordWrap
                verticalAlignment: Text.AlignVCenter
                font {
                    pixelSize: 13
                    bold: true
                }
                color: pluginInfo.color

            }

            Text {
                text: model.description
                width: parent.width
                height: 36
                clip: true
                wrapMode: Text.WordWrap
                color: pluginInfo.color
                elide: Text.ElideRight
            }
        }

        // Author info
        Column {
            id: authorInfo
            width: 192
            height: parent.height
            anchors {
                top: parent.top
                topMargin: UM.Theme.getSize("default_margin").height
                right: pluginActions.left
                rightMargin: UM.Theme.getSize("default_margin").width
            }

            Label {
                text: "<a href=\"mailto:"+model.author_email+"?Subject=Cura: "+model.name+"\">"+model.author+"</a>"
                width: parent.width
                height: 24
                wrapMode: Text.WordWrap
                verticalAlignment: Text.AlignVCenter
                horizontalAlignment: Text.AlignLeft
                onLinkActivated: Qt.openUrlExternally("mailto:"+model.author_email+"?Subject=Cura: "+model.name+" Plugin")
                color: model.enabled ? UM.Theme.getColor("text") : UM.Theme.getColor("lining")
            }
        }

        // Plugin actions
        Row {
            id: pluginActions

            width: 96
            height: parent.height
            anchors {
                top: parent.top
                right: parent.right
                topMargin: UM.Theme.getSize("default_margin").height
            }
            layoutDirection: Qt.RightToLeft
            spacing: UM.Theme.getSize("default_margin").width

            // For 3rd-Party Plugins:
            Button {
                id: installButton
                text: {
                    if ( manager.isDownloading && pluginList.activePlugin == model ) {
                        return catalog.i18nc( "@action:button", "Cancel" );
                    } else {
                        if (model.can_upgrade) {
                            return catalog.i18nc("@action:button", "Update");
                        }
                        return catalog.i18nc("@action:button", "Install");
                    }
                }
                visible: model.external && ((model.status !== "installed") || model.can_upgrade)
                style: ButtonStyle {
                    background: Rectangle {
                        implicitWidth: 96
                        implicitHeight: 30
                        color: "transparent"
                        border {
                            width: 1
                            color: UM.Theme.getColor("lining")
                        }
                    }
                    label: Label {
                        text: control.text
                        color: UM.Theme.getColor("text")
                        verticalAlignment: Text.AlignVCenter
                        horizontalAlignment: Text.AlignHCenter
                    }
                }
                onClicked: {
                    if ( manager.isDownloading && pluginList.activePlugin == model ) {
                        manager.cancelDownload();
                    } else {
                        pluginList.activePlugin = model;
                        if ( model.can_upgrade ) {
                            manager.downloadAndInstallPlugin( model.update_url );
                        } else {
                            manager.downloadAndInstallPlugin( model.file_location );
                        }

                    }
                }
            }
            Button {
                id: removeButton
                text: "Uninstall"
                visible: model.external && model.status == "installed"
                enabled: !manager.isDownloading
                style: ButtonStyle {
                    background: Rectangle {
                        implicitWidth: 96
                        implicitHeight: 30
                        color: "transparent"
                        border {
                            width: 1
                            color: UM.Theme.getColor("lining")
                        }
                    }
                    label: Text {
                        text: control.text
                        color: UM.Theme.getColor("text")
                        verticalAlignment: Text.AlignVCenter
                        horizontalAlignment: Text.AlignHCenter
                    }
                }
                onClicked: manager.removePlugin( model.id )
            }

            // For Ultimaker Plugins:
            Button {
                id: enableButton
                text: "Enable"
                visible: !model.external && model.enabled == false
                style: ButtonStyle {
                    background: Rectangle {
                        implicitWidth: 96
                        implicitHeight: 30
                        color: "transparent"
                        border {
                            width: 1
                            color: UM.Theme.getColor("lining")
                        }
                    }
                    label: Text {
                        text: control.text
                        color: UM.Theme.getColor("text")
                        verticalAlignment: Text.AlignVCenter
                        horizontalAlignment: Text.AlignHCenter
                    }
                }
                onClicked: {
                    manager.enablePlugin(model.id);
                }
            }
            Button {
                id: disableButton
                text: "Disable"
                visible: !model.external && model.enabled == true
                style: ButtonStyle {
                    background: Rectangle {
                        implicitWidth: 96
                        implicitHeight: 30
                        color: "transparent"
                        border {
                            width: 1
                            color: UM.Theme.getColor("lining")
                        }
                    }
                    label: Text {
                        text: control.text
                        color: UM.Theme.getColor("text")
                        verticalAlignment: Text.AlignVCenter
                        horizontalAlignment: Text.AlignHCenter
                    }
                }
                onClicked: {
                    manager.disablePlugin(model.id);
                }
            }
            /*
            Rectangle {
                id: removeControls
                visible: model.status == "installed" && model.enabled
                width: 96
                height: 30
                color: "transparent"
                Button {
                    id: removeButton
                    text: "Disable"
                    enabled: {
                        if ( manager.isDownloading && pluginList.activePlugin == model ) {
                            return false;
                        } else if ( model.required ) {
                            return false;
                        } else {
                            return true;
                        }
                    }
                    onClicked: {
                        manager.disablePlugin(model.id);
                    }
                    style: ButtonStyle {
                        background: Rectangle {
                            color: "white"
                            implicitWidth: 96
                            implicitHeight: 30
                            border {
                                width: 1
                                color: UM.Theme.getColor("lining")
                            }
                        }
                        label: Text {
                            verticalAlignment: Text.AlignVCenter
                            color: "grey"
                            text: control.text
                            horizontalAlignment: Text.AlignLeft
                        }
                    }
                }
                Button {
                    id: removeDropDown
                    property bool open: false
                    UM.RecolorImage {
                        anchors.centerIn: parent
                        height: 10
                        width: 10
                        source: UM.Theme.getIcon("arrow_bottom")
                        color: "grey"
                    }
                    enabled: {
                        if ( manager.isDownloading && pluginList.activePlugin == model ) {
                            return false;
                        } else if ( model.required ) {
                            return false;
                        } else {
                            return true;
                        }
                    }
                    anchors.right: parent.right
                    style: ButtonStyle {
                        background: Rectangle {
                            color: "transparent"
                            implicitWidth: 30
                            implicitHeight: 30
                        }
                        label: Text {
                            verticalAlignment: Text.AlignVCenter
                            color: "grey"
                            text: control.text
                            horizontalAlignment: Text.AlignHCenter
                        }
                    }



                    // For the disable option:
                    // onClicked: pluginList.model.setEnabled(model.id, checked)

                    onClicked: {
                        if ( !removeDropDown.open ) {
                            removeDropDown.open = true
                        }
                        else {
                            removeDropDown.open = false
                        }
                    }
                }

                Rectangle {
                    id: divider
                    width: 1
                    height: parent.height
                    anchors.right: removeDropDown.left
                    color: UM.Theme.getColor("lining")
                }

                Column {
                    id: options
                    anchors {
                        top: removeButton.bottom
                        left: parent.left
                        right: parent.right
                    }
                    height: childrenRect.height
                    visible: removeDropDown.open

                    Button {
                        id: disableButton
                        text: "Remove"
                        height: 30
                        width: parent.width
                        onClicked: {
                            removeDropDown.open = false;
                            manager.removePlugin( model.id );
                        }
                    }
                }
            }
            */
            /*
            Button {
                id: enableButton
                visible: !model.enabled && model.status == "installed"
                onClicked: manager.enablePlugin( model.id );

                text: "Enable"
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
                id: updateButton
                visible: model.status == "installed" && model.can_upgrade && model.enabled
                // visible: model.already_installed
                text: {
                    // If currently downloading:
                    if ( manager.isDownloading && pluginList.activePlugin == model ) {
                        return catalog.i18nc( "@action:button", "Cancel" );
                    } else {
                        return catalog.i18nc("@action:button", "Update");
                    }
                }
                style: ButtonStyle {
                    background: Rectangle {
                        color: UM.Theme.getColor("primary")
                        implicitWidth: 96
                        implicitHeight: 30
                        // radius: 4
                    }
                    label: Text {
                        verticalAlignment: Text.AlignVCenter
                        color: "white"
                        text: control.text
                        horizontalAlignment: Text.AlignHCenter
                    }
                }
            }
            Button {
                id: externalControls
                visible: model.status == "available" ? true : false
                text: {
                    // If currently downloading:
                    if ( manager.isDownloading && pluginList.activePlugin == model ) {
                        return catalog.i18nc( "@action:button", "Cancel" );
                    } else {
                        return catalog.i18nc("@action:button", "Install");
                    }
                }
                onClicked: {
                    if ( manager.isDownloading && pluginList.activePlugin == model ) {
                        manager.cancelDownload();
                    } else {
                        pluginList.activePlugin = model;
                        manager.downloadAndInstallPlugin( model.file_location );
                    }
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
                        color: "grey"
                        text: control.text
                        horizontalAlignment: Text.AlignHCenter
                    }
                }
            }
            */
            ProgressBar {
                id: progressbar
                minimumValue: 0;
                maximumValue: 100
                anchors.left: installButton.left
                anchors.right: installButton.right
                anchors.top: installButton.bottom
                anchors.topMargin: 4
                value: manager.isDownloading ? manager.downloadProgress : 0
                visible: manager.isDownloading && pluginList.activePlugin == model
                style: ProgressBarStyle {
                    background: Rectangle {
                        color: "lightgray"
                        implicitHeight: 6
                    }
                    progress: Rectangle {
                        color: UM.Theme.getColor("primary")
                    }
                }
            }

        }
    }
}
