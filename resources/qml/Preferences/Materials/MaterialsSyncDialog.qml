//Copyright (c) 2022 Ultimaker B.V.
//Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Dialogs
import QtQuick.Layouts 1.15
import QtQuick.Window 2.1

import Cura 1.1 as Cura
import UM 1.6 as UM

UM.Window
{
    id: materialsSyncDialog
    property variant catalog: UM.I18nCatalog { name: "cura" }

    title: catalog.i18nc("@title:window", "Sync materials with printers")
    minimumWidth: UM.Theme.getSize("modal_window_minimum").width
    minimumHeight: UM.Theme.getSize("modal_window_minimum").height
    width: minimumWidth
    height: minimumHeight
    modality: Qt.ApplicationModal
    color: UM.Theme.getColor("main_background")

    property variant syncModel
    property alias pageIndex: swipeView.currentIndex
    property alias syncStatusText: syncStatusLabel.text
    property bool hasExportedUsb: false

    SwipeView
    {
        id: swipeView
        anchors.fill: parent
        interactive: false

        Item
        {
            id: introPage

            ColumnLayout
            {
                spacing: UM.Theme.getSize("default_margin").height
                anchors.fill: parent
                anchors.margins: UM.Theme.getSize("default_margin").width

                UM.Label
                {
                    text: catalog.i18nc("@title:header", "Sync materials with printers")
                    font: UM.Theme.getFont("large_bold")
                    Layout.fillWidth: true
                }
                UM.Label
                {
                    text: catalog.i18nc("@text", "Following a few simple steps, you will be able to synchronize all your material profiles with your printers.")
                    font: UM.Theme.getFont("medium")
                    Layout.fillWidth: true
                }

                Image
                {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    source: UM.Theme.getImage("material_ecosystem")
                    fillMode: Image.PreserveAspectFit
                    sourceSize.width: width
                }

                Item
                {
                    Layout.preferredHeight: childrenRect.height
                    Layout.alignment: Qt.AlignBottom
                    Layout.fillWidth: true

                    Cura.TertiaryButton
                    {
                        text: catalog.i18nc("@button", "Why do I need to sync material profiles?")
                        iconSource: UM.Theme.getIcon("LinkExternal")
                        isIconOnRightSide: true
                        onClicked: Qt.openUrlExternally("https://support.ultimaker.com/hc/en-us/articles/360013137919?utm_source=cura&utm_medium=software&utm_campaign=sync-material-printer-why")
                    }

                    Cura.PrimaryButton
                    {
                        anchors.right: parent.right
                        text: catalog.i18nc("@button", "Start")
                        onClicked:
                        {
                            if(Cura.API.account.isLoggedIn)
                            {
                                if(Cura.API.account.permissions.includes("digital-factory.printer.write"))
                                {
                                    swipeView.currentIndex += 2; //Skip sign in page. Continue to sync via cloud.
                                }
                                else
                                {
                                    //Logged in, but no permissions to start syncing. Direct them to USB.
                                    swipeView.currentIndex = removableDriveSyncPage.SwipeView.index;
                                }
                            }
                            else
                            {
                                swipeView.currentIndex += 1;
                            }
                        }
                    }
                }
            }
        }

        Item
        {
            id: signinPage

            // While this page is active, continue to the next page if the user logs in.
            Connections
            {
                target: Cura.API.account
                function onLoginStateChanged(is_logged_in)
                {
                    if(is_logged_in && signinPage.SwipeView.isCurrentItem)
                    {
                        if(Cura.API.account.permissions.includes("digital-factory.printer.write"))
                        {
                            swipeView.currentIndex += 1;
                        }
                        else
                        {
                            //Logged in, but no permissions to start syncing. Direct them to USB.
                            swipeView.currentIndex = removableDriveSyncPage.SwipeView.index;
                        }
                    }
                }
            }

            ColumnLayout
            {
                spacing: UM.Theme.getSize("default_margin").height
                anchors.fill: parent
                anchors.margins: UM.Theme.getSize("default_margin").width

                UM.Label
                {
                    text: catalog.i18nc("@title:header", "Sign in")
                    font: UM.Theme.getFont("large_bold")
                    Layout.fillWidth: true
                }
                UM.Label
                {
                    text: catalog.i18nc("@text", "To automatically sync the material profiles with all your printers connected to Digital Factory you need to be signed in in Cura.")
                    font: UM.Theme.getFont("medium")
                    Layout.fillWidth: true
                }

                Image
                {
                    Layout.alignment: Qt.AlignCenter
                    Layout.preferredWidth: parent.width / 2
                    source: UM.Theme.getImage("first_run_ultimaker_cloud")
                    Layout.fillHeight: true
                    sourceSize.width: width
                    fillMode: Image.PreserveAspectFit
                }

                Item
                {
                    Layout.preferredHeight: childrenRect.height
                    Layout.alignment: Qt.AlignBottom
                    Layout.fillWidth: true

                    Cura.SecondaryButton
                    {
                        anchors.left: parent.left
                        text: catalog.i18nc("@button", "Sync materials with USB")
                        onClicked: swipeView.currentIndex = removableDriveSyncPage.SwipeView.index
                    }
                    Cura.PrimaryButton
                    {
                        anchors.right: parent.right
                        text: catalog.i18nc("@button", "Sign in")
                        onClicked: Cura.API.account.login()
                    }
                }
            }
        }

        Item
        {
            id: printerListPage

            ColumnLayout
            {
                spacing: UM.Theme.getSize("default_margin").height
                anchors.fill: parent
                anchors.margins: UM.Theme.getSize("default_margin").width
                visible: cloudPrinterList.count > 0

                Row
                {
                    spacing: UM.Theme.getSize("default_margin").width

                    states: [
                        State
                        {
                            name: "idle"
                            when: typeof syncModel === "undefined" || syncModel.exportUploadStatus == "idle" || syncModel.exportUploadStatus == "uploading"
                            PropertyChanges { target: printerListHeader; text: catalog.i18nc("@title:header", "The following printers will receive the new material profiles:") }
                            PropertyChanges { target: printerListHeaderIcon; status: UM.StatusIcon.Status.NEUTRAL; width: 0 }
                        },
                        State
                        {
                            name: "error"
                            when: typeof syncModel !== "undefined" && syncModel.exportUploadStatus == "error"
                            PropertyChanges { target: printerListHeader; text: catalog.i18nc("@title:header", "Something went wrong when sending the materials to the printers.") }
                            PropertyChanges { target: printerListHeaderIcon; status: UM.StatusIcon.Status.ERROR }
                        },
                        State
                        {
                            name: "success"
                            when: typeof syncModel !== "undefined" && syncModel.exportUploadStatus == "success"
                            PropertyChanges { target: printerListHeader; text: catalog.i18nc("@title:header", "Material profiles successfully synced with the following printers:") }
                            PropertyChanges { target: printerListHeaderIcon; status: UM.StatusIcon.Status.POSITIVE }
                        }
                    ]

                    UM.StatusIcon
                    {
                        id: printerListHeaderIcon
                        width: UM.Theme.getSize("section_icon").width
                        height: UM.Theme.getSize("section_icon").height
                        anchors.verticalCenter: parent.verticalCenter
                    }
                    UM.Label
                    {
                        id: printerListHeader
                        anchors.verticalCenter: parent.verticalCenter
                        //Text is always defined by the states above.
                        font: UM.Theme.getFont("large_bold")
                    }
                }
                Row
                {
                    Layout.fillWidth: true
                    Layout.preferredHeight: childrenRect.height

                    UM.Label
                    {
                        id: syncStatusLabel
                        anchors.left: parent.left
                        elide: Text.ElideRight
                        visible: text !== ""
                        font: UM.Theme.getFont("medium")
                    }
                    Cura.TertiaryButton
                    {
                        id: troubleshootingLink
                        anchors.right: parent.right
                        text: catalog.i18nc("@button", "Troubleshooting")
                        visible: typeof syncModel !== "undefined" && syncModel.exportUploadStatus == "error"
                        iconSource: UM.Theme.getIcon("LinkExternal")
                        onClicked: Qt.openUrlExternally("https://support.ultimaker.com/hc/en-us/articles/360012019239?utm_source=cura&utm_medium=software&utm_campaign=sync-material-wizard-troubleshoot-cloud-printer")
                    }
                }
                ListView
                {
                    id: printerList
                    Layout.fillWidth: true
                    Layout.fillHeight: true

                    clip: true
                    ScrollBar.vertical: UM.ScrollBar
                    {
                        id: printerListScrollBar
                    }
                    spacing: UM.Theme.getSize("default_margin").height

                    model: cloudPrinterList
                    delegate: Rectangle
                    {
                        id: delegateContainer
                        color: "transparent"
                        border.color: UM.Theme.getColor("lining")
                        border.width: UM.Theme.getSize("default_lining").width
                        width: printerList.width - printerListScrollBar.width
                        height: UM.Theme.getSize("machine_selector_icon").height + 2 * UM.Theme.getSize("default_margin").height

                        property string syncStatus:
                        {
                            var printer_id = model.metadata["host_guid"]
                            if(syncModel.printerStatus[printer_id] === undefined) //No status information available. Could be added after we started syncing.
                            {
                                return "idle";
                            }
                            return syncModel.printerStatus[printer_id];
                        }

                        Cura.IconWithText
                        {
                            anchors
                            {
                                verticalCenter: parent.verticalCenter
                                left: parent.left
                                leftMargin: Math.round(parent.height - height) / 2 //Equal margin on the left as above and below.
                                right: parent.right
                                rightMargin: Math.round(parent.height - height) / 2
                            }

                            text: model.name
                            font: UM.Theme.getFont("medium")

                            source: UM.Theme.getIcon("Printer", "medium")
                            iconColor: UM.Theme.getColor("machine_selector_printer_icon")
                            iconSize: UM.Theme.getSize("machine_selector_icon").width

                            //Printer status badge (always cloud, but whether it's online or offline).
                            UM.ColorImage
                            {
                                width: UM.Theme.getSize("printer_status_icon").width
                                height: UM.Theme.getSize("printer_status_icon").height
                                anchors
                                {
                                    bottom: parent.bottom
                                    bottomMargin: -Math.round(height / 6)
                                    left: parent.left
                                    leftMargin: parent.iconSize - Math.round(width * 5 / 6)
                                }

                                source: UM.Theme.getIcon("CloudBadge", "low")
                                color: UM.Theme.getColor("primary")

                                //Make a themeable circle in the background so we can change it in other themes.
                                Rectangle
                                {
                                    anchors.centerIn: parent
                                    width: parent.width - 1.5 //1.5 pixels smaller (at least sqrt(2), regardless of pixel scale) so that the circle doesn't show up behind the icon due to anti-aliasing.
                                    height: parent.height - 1.5
                                    radius: width / 2
                                    color: UM.Theme.getColor("connection_badge_background")
                                    z: parent.z - 1
                                }
                            }
                        }

                        UM.ColorImage
                        {
                            id: printerSpinner
                            width: UM.Theme.getSize("section_icon").width
                            height: width
                            anchors.verticalCenter: parent.verticalCenter
                            anchors.right: parent.right
                            anchors.rightMargin: Math.round((parent.height - height) / 2) //Same margin on the right as above and below.

                            visible: delegateContainer.syncStatus === "uploading"
                            source: UM.Theme.getIcon("ArrowDoubleCircleRight")
                            color: UM.Theme.getColor("primary")

                            RotationAnimator
                            {
                                target: printerSpinner
                                from: 0
                                to: 360
                                duration: 1000
                                loops: Animation.Infinite
                                running: true
                            }
                        }
                        UM.StatusIcon
                        {
                            width: UM.Theme.getSize("section_icon").width
                            height: width
                            anchors.verticalCenter: parent.verticalCenter
                            anchors.right: parent.right
                            anchors.rightMargin: Math.round((parent.height - height) / 2) //Same margin on the right as above and below.

                            visible: delegateContainer.syncStatus === "failed" || delegateContainer.syncStatus === "success"
                            status: delegateContainer.syncStatus === "success" ? UM.StatusIcon.Status.POSITIVE : UM.StatusIcon.Status.ERROR
                        }
                    }

                    footer: Item
                    {
                        width: printerList.width - printerListScrollBar.width
                        height: childrenRect.height + UM.Theme.getSize("default_margin").height
                        visible: includeOfflinePrinterList.count - cloudPrinterList.count > 0 && typeof syncModel !== "undefined" && syncModel.exportUploadStatus === "idle"
                        Rectangle
                        {
                            anchors.top: parent.top
                            anchors.left: parent.left
                            anchors.right: parent.right
                            border.color: UM.Theme.getColor("lining")
                            border.width: UM.Theme.getSize("default_lining").width
                            anchors.topMargin: UM.Theme.getSize("default_margin").height
                            height: childrenRect.height + 2 * UM.Theme.getSize("thick_margin").height

                            color: "transparent"

                            GridLayout
                            {
                                columns: 3
                                rows: 2
                                anchors.top: parent.top
                                anchors.left: parent.left
                                anchors.right: parent.right
                                anchors.leftMargin: UM.Theme.getSize("thick_margin").width
                                anchors.rightMargin: UM.Theme.getSize("thick_margin").width
                                anchors.topMargin: UM.Theme.getSize("thick_margin").height
                                anchors.bottomMargin: UM.Theme.getSize("thick_margin").height
                                columnSpacing: UM.Theme.getSize("default_margin").width
                                rowSpacing: UM.Theme.getSize("default_margin").height

                                UM.StatusIcon
                                {
                                    Layout.preferredWidth: UM.Theme.getSize("section_icon").width
                                    Layout.preferredHeight: UM.Theme.getSize("section_icon").height
                                    status: UM.StatusIcon.Status.WARNING
                                }

                                UM.Label
                                {
                                    Layout.fillWidth: true
                                    Layout.alignment: Qt.AlignVCenter
                                    text: catalog.i18nc("@text Asking the user whether printers are missing in a list.", "Printers missing?")
                                      + "\n"
                                      + catalog.i18nc("@text", "Make sure all your printers are turned ON and connected to Digital Factory.")
                                    font: UM.Theme.getFont("medium")
                                    elide: Text.ElideRight
                                }

                                Cura.SecondaryButton
                                {
                                    id: refreshListButton
                                    Layout.alignment: Qt.AlignVCenter
                                    readonly property int _AccountSyncState_SYNCING: 0
                                    visible: Cura.API.account.syncState != _AccountSyncState_SYNCING
                                    enabled: visible
                                    text: catalog.i18nc("@button", "Refresh List")
                                    iconSource: UM.Theme.getIcon("ArrowDoubleCircleRight")
                                    onClicked: Cura.API.account.sync(true)
                                }

                                Item
                                {
                                    width: childrenRect.width
                                    Layout.alignment: Qt.AlignVCenter
                                    height: refreshListButton.height
                                    visible: !refreshListButton.visible

                                    UM.ColorImage
                                    {
                                        id: refreshingIcon
                                        height: UM.Theme.getSize("action_button_icon").height
                                        width: height
                                        anchors.verticalCenter: refreshingLabel.verticalCenter
                                        source: UM.Theme.getIcon("ArrowDoubleCircleRight")
                                        color: UM.Theme.getColor("primary")

                                        RotationAnimator
                                        {
                                            target: refreshingIcon
                                            from: 0
                                            to: 360
                                            duration: 1000
                                            loops: Animation.Infinite
                                            running: true
                                        }
                                    }
                                    UM.Label
                                    {
                                        id: refreshingLabel
                                        anchors.left: refreshingIcon.right
                                        anchors.leftMargin: UM.Theme.getSize("narrow_margin").width
                                        text: catalog.i18nc("@button", "Refreshing...")
                                        color: UM.Theme.getColor("primary")
                                        font: UM.Theme.getFont("medium")
                                    }
                                }

                                Cura.TertiaryButton
                                {
                                    id: printerListTroubleshooting
                                    Layout.column: 1
                                    Layout.row: 1
                                    Layout.fillWidth: true
                                    leftPadding: 0
                                    text: catalog.i18nc("@button", "Troubleshooting")
                                    iconSource: UM.Theme.getIcon("LinkExternal")
                                    onClicked: Qt.openUrlExternally("https://support.ultimaker.com/hc/en-us/articles/360012019239?utm_source=cura&utm_medium=software&utm_campaign=sync-material-wizard-troubleshoot-cloud-printer")
                                }
                            }
                        }
                    }
                }
                Item
                {
                    Layout.fillWidth: true
                    Layout.preferredHeight: childrenRect.height
                    Layout.alignment: Qt.AlignBottom

                    Cura.SecondaryButton
                    {
                        anchors.left: parent.left
                        text: catalog.i18nc("@button", "Sync materials with USB")
                        onClicked: swipeView.currentIndex = removableDriveSyncPage.SwipeView.index
                    }
                    Cura.PrimaryButton
                    {
                        id: syncButton
                        anchors.right: parent.right
                        text:
                        {
                            if(typeof syncModel !== "undefined" && syncModel.exportUploadStatus == "error")
                            {
                                return catalog.i18nc("@button", "Try again");
                            }
                            if(typeof syncModel !== "undefined" && syncModel.exportUploadStatus == "success")
                            {
                                return catalog.i18nc("@button", "Done");
                            }
                            return catalog.i18nc("@button", "Sync");
                        }
                        onClicked:
                        {
                            if(typeof syncModel !== "undefined" && syncModel.exportUploadStatus == "success")
                            {
                                materialsSyncDialog.close();
                            }
                            else
                            {
                                syncModel.exportUpload();
                            }
                        }
                        visible:
                        {
                            if(!syncModel) //When the dialog is created, this is not set yet.
                            {
                                return true;
                            }
                            return syncModel.exportUploadStatus != "uploading";
                        }
                    }
                    Item
                    {
                        anchors.right: parent.right
                        width: childrenRect.width
                        height: syncButton.height

                        visible: !syncButton.visible

                        UM.ColorImage
                        {
                            id: syncingIcon
                            height: UM.Theme.getSize("action_button_icon").height
                            width: height
                            anchors.verticalCenter: syncingLabel.verticalCenter

                            source: UM.Theme.getIcon("ArrowDoubleCircleRight")
                            color: UM.Theme.getColor("primary")

                            RotationAnimator
                            {
                                target: syncingIcon
                                from: 0
                                to: 360
                                duration: 1000
                                loops: Animation.Infinite
                                running: true
                            }
                        }
                        UM.Label
                        {
                            id: syncingLabel
                            anchors.left: syncingIcon.right
                            anchors.leftMargin: UM.Theme.getSize("narrow_margin").width

                            text: catalog.i18nc("@button", "Syncing")
                            color: UM.Theme.getColor("primary")
                            font: UM.Theme.getFont("medium")
                        }
                    }
                }
            }

            // Placeholder for when the user has no cloud printers.
            ColumnLayout
            {
                spacing: UM.Theme.getSize("default_margin").height
                anchors.fill: parent
                anchors.margins: UM.Theme.getSize("default_margin").width
                visible: cloudPrinterList.count == 0

                UM.Label
                {
                    text: catalog.i18nc("@title:header", "No printers found")
                    font: UM.Theme.getFont("large_bold")
                    Layout.fillWidth: true
                }

                Item
                {
                    Layout.fillWidth: true
                    Layout.fillHeight: true

                    Image
                    {
                        anchors.fill: parent
                        source: UM.Theme.getImage("3d_printer_faded")
                        sourceSize.width: width
                        fillMode: Image.PreserveAspectFit
                    }
                }

                UM.Label
                {
                    text: catalog.i18nc("@text", "It seems like you don't have any compatible printers connected to Digital Factory. Make sure your printer is connected and it's running the latest firmware.")
                    Layout.fillWidth: true
                    horizontalAlignment: Text.AlignHCenter
                }

                Item
                {
                    Layout.fillWidth: true
                    Layout.preferredHeight: parent.height / 4
                    Cura.TertiaryButton
                    {
                        text: catalog.i18nc("@button", "Learn how to connect your printer to Digital Factory")
                        iconSource: UM.Theme.getIcon("LinkExternal")
                        onClicked: Qt.openUrlExternally("https://support.ultimaker.com/hc/en-us/articles/360012019239?utm_source=cura&utm_medium=software&utm_campaign=sync-material-wizard-add-cloud-printer")
                        anchors.horizontalCenter: parent.horizontalCenter
                        maximumWidth: parent.width
                    }
                }

                Item
                {
                    Layout.preferredHeight: childrenRect.height
                    Layout.alignment: Qt.AlignBottom
                    Layout.fillWidth: true

                    Cura.SecondaryButton
                    {
                        anchors.left: parent.left
                        text: catalog.i18nc("@button", "Sync materials with USB")
                        onClicked: swipeView.currentIndex = removableDriveSyncPage.SwipeView.index
                    }

                    RowLayout
                    {
                        anchors.right: parent.right
                        spacing: UM.Theme.getSize("default_margin").width

                        Cura.SecondaryButton
                        {
                            text: catalog.i18nc("@button", "Refresh")
                            iconSource: UM.Theme.getIcon("ArrowDoubleCircleRight")
                            outlineColor: "transparent"
                            onClicked: Cura.API.account.sync(true)
                        }

                        Cura.PrimaryButton
                        {
                            id: disabledSyncButton
                            text: catalog.i18nc("@button", "Sync")
                            enabled: false // If there are no printers, always disable this button.
                        }
                    }
                }
            }
        }

        Item
        {
            id: removableDriveSyncPage

            ColumnLayout
            {
                spacing: UM.Theme.getSize("default_margin").height
                anchors.fill: parent
                anchors.margins: UM.Theme.getSize("default_margin").width

                UM.Label
                {
                    text: catalog.i18nc("@title:header", "Sync material profiles via USB")
                    font: UM.Theme.getFont("large_bold")
                    Layout.fillWidth: true
                }
                UM.Label
                {
                    text: catalog.i18nc("@text In the UI this is followed by a list of steps the user needs to take.", "Follow the following steps to load the new material profiles to your printer.")
                    font: UM.Theme.getFont("medium")
                    Layout.fillWidth: true
                }

                RowLayout
                {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    spacing: UM.Theme.getSize("default_margin").width

                    Item
                    {
                        Layout.preferredWidth: parent.width / 3
                        Layout.fillHeight: true

                        Image
                        {
                            anchors.fill: parent
                            source: UM.Theme.getImage("insert_usb")
                            verticalAlignment: Image.AlignVCenter
                            horizontalAlignment: Image.AlignHCenter
                            fillMode: Image.PreserveAspectFit
                            sourceSize.width: width
                        }
                    }

                    UM.Label
                    {
                        Layout.alignment: Qt.AlignCenter
                        Layout.fillWidth: true
                        text: "1. " + catalog.i18nc("@text", "Click the export material archive button.")
                          + "\n2. " + catalog.i18nc("@text", "Save the .umm file on a USB stick.")
                          + "\n3. " + catalog.i18nc("@text", "Insert the USB stick into your printer and launch the procedure to load new material profiles.")
                        font: UM.Theme.getFont("medium")
                    }
                }

                Cura.TertiaryButton
                {
                    Layout.fillWidth: true
                    text: catalog.i18nc("@button", "How to load new material profiles to my printer")
                    iconSource: UM.Theme.getIcon("LinkExternal")
                    onClicked: Qt.openUrlExternally("https://support.ultimaker.com/hc/en-us/articles/4403319801106/?utm_source=cura&utm_medium=software&utm_campaign=add-material-profiles-via-usb")
                }

                Item
                {
                    Layout.preferredHeight: childrenRect.height
                    Layout.alignment: Qt.AlignBottom
                    Layout.fillWidth: true

                    Cura.SecondaryButton
                    {
                        anchors.left: parent.left
                        text: catalog.i18nc("@button", "Back")
                        onClicked: swipeView.currentIndex = 0 //Reset to first page.
                    }
                    Cura.PrimaryButton
                    {
                        id: exportUsbButton
                        anchors.right: parent.right

                        property bool hasExported: false
                        text: materialsSyncDialog.hasExportedUsb ? catalog.i18nc("@button", "Done") : catalog.i18nc("@button", "Export material archive")
                        onClicked:
                        {
                            if(!materialsSyncDialog.hasExportedUsb)
                            {
                                exportUsbDialog.currentFolder = `${syncModel.getPreferredExportAllPath()}/materials.umm`;
                                exportUsbDialog.open();
                            }
                            else
                            {
                                materialsSyncDialog.close();
                            }
                        }
                    }
                }
            }
        }
    }

    property variant cloudPrinterList: Cura.GlobalStacksModel
    {
        filterConnectionType: 3 //Only show cloud connections.
        filterOnlineOnly: true //Only show printers that are online.
        filterCapabilities: ["import_material"] //Only show printers that can receive the material profiles.
    }

    property variant includeOfflinePrinterList: Cura.GlobalStacksModel
    {
        //In order to show a refresh button only when there are offline cloud printers, we need to know if there are any offline printers.
        //A global stacks model without the filter for online-only printers allows this.
        filterConnectionType: 3 //Still only show cloud connections.
    }

    property variant exportUsbDialog: FileDialog
    {
        title: catalog.i18nc("@title:window", "Export All Materials")
        nameFilters: ["Material archives (*.umm)", "All files (*)"]
        fileMode: FileDialog.SaveFile
        onAccepted:
        {
            syncModel.exportAll(selectedFile);
            CuraApplication.setDefaultPath("dialog_material_path", folder);
            materialsSyncDialog.hasExportedUsb = true;
        }
    }
}
