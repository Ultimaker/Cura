import UM 1.1 as UM
import QtQuick 2.2
import QtQuick.Dialogs 1.1
import QtQuick.Window 2.2
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.4

UM.Dialog {
    id: base

    title: catalog.i18nc("@title:tab", "Plugins");
    width: 800 * screenScaleFactor
    height: 450 * screenScaleFactor
    minimumWidth: 350 * screenScaleFactor
    minimumHeight: 350 * screenScaleFactor
    Item
    {
        anchors.fill: parent
        Item
        {
            id: topBar
            height: childrenRect.height;
            width: parent.width
            Label
            {
                id: introText
                text: catalog.i18nc("@label", "Here you can find a list of Third Party plugins.")
                width: parent.width
                height: 30
            }

            Button
            {
                id: refresh
                text: catalog.i18nc("@action:button", "Refresh")
                onClicked: manager.requestPluginList()
                anchors.right: parent.right
                enabled: !manager.isDownloading
            }
        }
        ScrollView
        {
            width: parent.width
            anchors.top: topBar.bottom
            anchors.bottom: bottomBar.top
            anchors.bottomMargin: UM.Theme.getSize("default_margin").height
            frameVisible: true
            ListView {
                id: pluginList
                model: manager.pluginsModel
                anchors.fill: parent

                property var activePlugin
                delegate: pluginDelegate
            }
        }
        Item
        {
            id: bottomBar
            width: parent.width
            height: closeButton.height
            anchors.bottom: parent.bottom
            anchors.left: parent.left


            Button
            {
                id: closeButton
                text: catalog.i18nc("@action:button", "Close")
                iconName: "dialog-close"
                onClicked:
                {
                    if (manager.isDownloading)
                    {
                        manager.cancelDownload()
                    }
                    base.close();
                }
                anchors.bottom: parent.bottom
                anchors.right: parent.right
            }
        }

        Item {
            Component {
                id: pluginDelegate

                Rectangle {
                    width: pluginList.width;
                    height: 96
                    color: index % 2 ? UM.Theme.getColor("secondary") : "white"

                    // Plugin info
                    Column {
                        id: pluginInfo
                        height: parent.height
                        anchors.left: parent.left
                        anchors.leftMargin: UM.Theme.getSize("default_margin").width
                        anchors.top: parent.top
                        anchors.topMargin: UM.Theme.getSize("default_margin").height
                        anchors.right: authorInfo.left
                        anchors.rightMargin: UM.Theme.getSize("default_margin").width

                        Label {
                            text: model.name
                            width: parent.width
                            height: 24
                            wrapMode: Text.WordWrap
                            verticalAlignment: Text.AlignVCenter
                            font {
                                pixelSize: 15
                                bold: true
                            }
                            color: model.enabled ? UM.Theme.getColor("text") : "grey"
                        }

                        Label {
                            text: model.short_description
                            width: parent.width
                            height: 72
                            wrapMode: Text.WordWrap
                        }
                    }

                    // Author info
                    Column {
                        id: authorInfo
                        width: 192
                        height: parent.height


                        anchors.top: parent.top
                        anchors.topMargin: UM.Theme.getSize("default_margin").height

                        anchors.right: pluginActions.left
                        anchors.rightMargin: UM.Theme.getSize("default_margin").width

                        Label {
                            text: model.author
                            width: parent.width
                            height: 24
                            wrapMode: Text.WordWrap
                            verticalAlignment: Text.AlignVCenter
                            horizontalAlignment: Text.AlignRight
                        }

                        Label {
                            text: "author@ultimaker.com"
                            width: parent.width
                            height: 72
                            wrapMode: Text.WordWrap
                            horizontalAlignment: Text.AlignRight
                        }
                    }

                    // Plugin actions
                    Row {
                        id: pluginActions
                        width: 180 + UM.Theme.getSize("default_margin").width
                        height: parent.height
                        anchors {
                            top: parent.top
                            right: parent.right
                            topMargin: UM.Theme.getSize("default_margin").height
                            rightMargin: UM.Theme.getSize("default_margin").width
                        }
                        layoutDirection: Qt.RightToLeft
                        spacing: UM.Theme.getSize("default_margin").width

                        Rectangle {
                            id: removeControls
                            visible: model.already_installed
                            width: 108
                            height: 30
                            color: "transparent"
                            Button {
                                id: removeButton
                                text: "Remove"
                                enabled: {
                                    if ( manager.isDownloading && pluginList.activePlugin == model ) {
                                        return false;
                                    } else {
                                        return true;
                                    }
                                }
                                style: ButtonStyle {
                                    background: Rectangle {
                                        color: white
                                        implicitWidth: 108
                                        implicitHeight: 30
                                        // radius: 4
                                        border {
                                            width: 1
                                            color: "grey"
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
                                    if ( model.required || ( manager.isDownloading && pluginList.activePlugin == model )) {
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
                                        // radius: 4
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
                                color: "grey"
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
                                    text: "Disable"
                                    height: 30
                                    width: parent.width
                                    onClicked: {
                                        removeDropDown.open = false
                                        model.setEnabled(model.id, checked)
                                    }
                                }
                            }
                        }



                        Button {
                            id: updateButton
                            // visible: model.already_installed && model.can_upgrade
                            visible: model.already_installed
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
                                    implicitWidth: 72
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
                            id: installButton
                            visible: !model.already_installed
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
                                    color: UM.Theme.getColor("primary")
                                    implicitWidth: 72
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
        }
        UM.I18nCatalog { id: catalog; name: "cura" }

        Connections
        {
            target: manager
            onShowLicenseDialog:
            {
                licenseDialog.pluginName = manager.getLicenseDialogPluginName();
                licenseDialog.licenseContent = manager.getLicenseDialogLicenseContent();
                licenseDialog.pluginFileLocation = manager.getLicenseDialogPluginFileLocation();
                licenseDialog.show();
            }
        }

        UM.Dialog
        {
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
    }
}
